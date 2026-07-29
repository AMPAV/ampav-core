"""Provider-neutral text chunking and text-span reassembly utilities."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import re
from typing import TypeVar

from .schema.segments import WordSegment
from .schema.text_span import TextSpan


WeightFunction = Callable[[str], int]
TTextSpan = TypeVar("TTextSpan", bound=TextSpan)


@dataclass(frozen=True)
class TextUnit:
    """An indivisible source-text range and its weight toward a tool limit.

    Offsets use Python string character indices in the original source text.
    ``weight`` is tool-defined: it may represent words, model tokens, bytes, or
    another positive measure.
    """

    begin_offset: int
    end_offset: int
    weight: int = 1

    def __post_init__(self) -> None:
        _validate_integer("begin_offset", self.begin_offset)
        _validate_integer("end_offset", self.end_offset)
        _validate_integer("weight", self.weight)
        if self.begin_offset < 0:
            raise ValueError("begin_offset must be greater than or equal to zero")
        if self.end_offset <= self.begin_offset:
            raise ValueError("end_offset must be greater than begin_offset")
        if self.weight <= 0:
            raise ValueError("weight must be greater than zero")


@dataclass(frozen=True)
class TextChunk:
    """A source-text window plus the subrange that owns returned spans.

    ``begin_offset:end_offset`` identifies the complete window sent to a tool.
    The owned offsets identify the non-overlapping source region whose results
    this chunk retains when overlapping windows are reassembled.
    """

    text: str
    begin_offset: int
    end_offset: int
    owned_begin_offset: int
    owned_end_offset: int

    def __post_init__(self) -> None:
        for name in (
            "begin_offset",
            "end_offset",
            "owned_begin_offset",
            "owned_end_offset",
        ):
            _validate_integer(name, getattr(self, name))
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if self.begin_offset < 0:
            raise ValueError("begin_offset must be greater than or equal to zero")
        if self.end_offset <= self.begin_offset:
            raise ValueError("end_offset must be greater than begin_offset")
        if len(self.text) != self.end_offset - self.begin_offset:
            raise ValueError("text length must match begin_offset:end_offset")
        if not (
            self.begin_offset
            <= self.owned_begin_offset
            < self.owned_end_offset
            <= self.end_offset
        ):
            raise ValueError("owned offsets must define a non-empty range within the chunk")


def text_to_units(
    text: str,
    *,
    weight_fn: WeightFunction | None = None,
) -> list[TextUnit]:
    """Split plain text at whitespace boundaries into contiguous text units.

    Each unit includes adjacent whitespace needed to make the returned ranges a
    complete partition of ``text``. This is a dependency-free chunk-boundary
    splitter, not a linguistic or model tokenizer. ``weight_fn`` receives each
    exact source substring and must return a positive integer.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []

    word_starts = [match.start() for match in re.finditer(r"\S+", text)]
    if not word_starts:
        return [TextUnit(0, len(text), _get_weight(text, weight_fn))]

    units: list[TextUnit] = []
    for index, word_start in enumerate(word_starts):
        begin_offset = 0 if index == 0 else word_start
        end_offset = word_starts[index + 1] if index + 1 < len(word_starts) else len(text)
        unit_text = text[begin_offset:end_offset]
        units.append(TextUnit(begin_offset, end_offset, _get_weight(unit_text, weight_fn)))
    return units


def words_to_text_units(
    words: Sequence[WordSegment],
    *,
    separator: str = " ",
    weight_fn: WeightFunction | None = None,
) -> tuple[str, list[TextUnit]]:
    """Build canonical transcript text and matching units in one traversal.

    Each unit corresponds to one rendered ``WordSegment`` and includes its
    following separator, except for the final word. This preserves the exact
    coordinate system later used by ``TextSpans.align_timestamps``.
    """
    if isinstance(words, (str, bytes)) or not isinstance(words, Sequence):
        raise TypeError("words must be a sequence of WordSegment objects")
    if not isinstance(separator, str):
        raise TypeError("separator must be a string")

    text_parts: list[str] = []
    units: list[TextUnit] = []
    offset = 0
    for index, word in enumerate(words):
        if not isinstance(word, WordSegment):
            raise TypeError(f"words[{index}] must be a WordSegment")
        rendered_word = word.to_str()
        if not rendered_word:
            raise ValueError(f"words[{index}] renders as empty text")
        unit_text = rendered_word
        if index + 1 < len(words):
            unit_text += separator
        begin_offset = offset
        offset += len(unit_text)
        text_parts.append(unit_text)
        units.append(TextUnit(begin_offset, offset, _get_weight(unit_text, weight_fn)))
    return "".join(text_parts), units


def chunk_text(
    text: str,
    units: Sequence[TextUnit],
    *,
    max_weight: int,
    overlap_weight: int = 0,
) -> list[TextChunk]:
    """Build weighted text windows with optional context overlap.

    ``max_weight`` limits the sum of unit weights in every complete window.
    ``overlap_weight`` is the maximum context weight added on each side of an
    owned range. Overlap is best effort because units are indivisible.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    _validate_integer("max_weight", max_weight)
    _validate_integer("overlap_weight", overlap_weight)
    if max_weight <= 0:
        raise ValueError("max_weight must be greater than zero")
    if overlap_weight < 0:
        raise ValueError("overlap_weight must be greater than or equal to zero")
    if overlap_weight * 2 >= max_weight:
        raise ValueError("overlap_weight must leave positive owned capacity")

    validated_units = _validate_units(text, units, max_weight=max_weight)
    if not validated_units:
        return []

    total_weight = sum(unit.weight for unit in validated_units)
    if total_weight <= max_weight:
        return [
            TextChunk(
                text=text,
                begin_offset=0,
                end_offset=len(text),
                owned_begin_offset=0,
                owned_end_offset=len(text),
            )
        ]

    owned_capacity = max_weight - 2 * overlap_weight
    owned_ranges = _partition_owned_ranges(validated_units, owned_capacity)
    chunks: list[TextChunk] = []
    for owned_start, owned_end in owned_ranges:
        window_start = owned_start
        window_end = owned_end
        window_weight = sum(unit.weight for unit in validated_units[owned_start:owned_end])

        left_weight = 0
        while window_start > 0:
            candidate = validated_units[window_start - 1]
            if left_weight + candidate.weight > overlap_weight:
                break
            if window_weight + candidate.weight > max_weight:
                break
            window_start -= 1
            left_weight += candidate.weight
            window_weight += candidate.weight

        right_weight = 0
        while window_end < len(validated_units):
            candidate = validated_units[window_end]
            if right_weight + candidate.weight > overlap_weight:
                break
            if window_weight + candidate.weight > max_weight:
                break
            window_end += 1
            right_weight += candidate.weight
            window_weight += candidate.weight

        begin_offset = validated_units[window_start].begin_offset
        end_offset = validated_units[window_end - 1].end_offset
        owned_begin_offset = validated_units[owned_start].begin_offset
        owned_end_offset = validated_units[owned_end - 1].end_offset
        chunks.append(
            TextChunk(
                text=text[begin_offset:end_offset],
                begin_offset=begin_offset,
                end_offset=end_offset,
                owned_begin_offset=owned_begin_offset,
                owned_end_offset=owned_end_offset,
            )
        )
    return chunks


def dechunk_text_spans(
    text: str,
    chunk_outputs: Sequence[tuple[TextChunk, Sequence[TTextSpan]]],
) -> list[TTextSpan]:
    """Rebase chunk-local spans into the original source-text coordinates.

    A rebased span is retained when its midpoint falls inside the chunk's owned
    range. Invalid offsets or text mismatches raise ``ValueError`` because core
    cannot safely guess where such a span belongs.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(chunk_outputs, Sequence):
        raise TypeError("chunk_outputs must be a sequence")
    if not chunk_outputs:
        if text:
            raise ValueError("chunk_outputs must cover non-empty text")
        return []

    rebased_spans: list[TTextSpan] = []
    expected_owned_begin = 0
    for chunk_index, (chunk, spans) in enumerate(chunk_outputs):
        _validate_chunk_against_source(chunk, text, chunk_index)
        if chunk.owned_begin_offset != expected_owned_begin:
            raise ValueError("chunk owned ranges must be ordered and contiguous")
        expected_owned_begin = chunk.owned_end_offset
        if isinstance(spans, (str, bytes)) or not isinstance(spans, Sequence):
            raise TypeError(f"chunk_outputs[{chunk_index}] spans must be a sequence")

        for span_index, span in enumerate(spans):
            if not isinstance(span, TextSpan):
                raise TypeError(
                    f"chunk_outputs[{chunk_index}] spans[{span_index}] must be a TextSpan"
                )
            local_begin = span.begin_offset
            local_end = span.end_offset
            if local_begin is None or local_end is None:
                raise ValueError(
                    f"chunk_outputs[{chunk_index}] spans[{span_index}] must include offsets"
                )
            if local_begin < 0 or local_end <= local_begin or local_end > len(chunk.text):
                raise ValueError(
                    f"chunk_outputs[{chunk_index}] spans[{span_index}] offsets are out of range"
                )
            if span.text != chunk.text[local_begin:local_end]:
                raise ValueError(
                    f"chunk_outputs[{chunk_index}] spans[{span_index}] text does not match offsets"
                )

            source_begin = chunk.begin_offset + local_begin
            source_end = chunk.begin_offset + local_end
            midpoint = (source_begin + source_end) / 2
            if chunk.owned_begin_offset <= midpoint < chunk.owned_end_offset:
                rebased_spans.append(
                    span.model_copy(
                        deep=True,
                        update={
                            "begin_offset": source_begin,
                            "end_offset": source_end,
                        },
                    )
                )

    if expected_owned_begin != len(text):
        raise ValueError("chunk owned ranges must cover the complete source text")
    rebased_spans.sort(key=lambda span: (span.begin_offset, span.end_offset))
    return rebased_spans


def _get_weight(text: str, weight_fn: WeightFunction | None) -> int:
    weight = 1 if weight_fn is None else weight_fn(text)
    _validate_integer("weight_fn result", weight)
    if weight <= 0:
        raise ValueError("weight_fn must return a positive integer")
    return weight


def _validate_units(
    text: str,
    units: Sequence[TextUnit],
    *,
    max_weight: int,
) -> list[TextUnit]:
    if isinstance(units, (str, bytes)) or not isinstance(units, Sequence):
        raise TypeError("units must be a sequence of TextUnit objects")
    if not text:
        if units:
            raise ValueError("empty text cannot have units")
        return []
    if not units:
        raise ValueError("units must cover non-empty text")

    validated_units = list(units)
    expected_begin = 0
    for index, unit in enumerate(validated_units):
        if not isinstance(unit, TextUnit):
            raise TypeError(f"units[{index}] must be a TextUnit")
        if unit.begin_offset != expected_begin:
            raise ValueError("units must be ordered, contiguous, and begin at zero")
        if unit.end_offset > len(text):
            raise ValueError(f"units[{index}] extends beyond the source text")
        if unit.weight > max_weight:
            raise ValueError(f"units[{index}] weight exceeds max_weight")
        expected_begin = unit.end_offset
    if expected_begin != len(text):
        raise ValueError("units must cover the complete source text")
    return validated_units


def _partition_owned_ranges(
    units: Sequence[TextUnit],
    owned_capacity: int,
) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start = 0
    while start < len(units):
        end = start
        weight = 0
        while end < len(units):
            candidate_weight = units[end].weight
            if end > start and weight + candidate_weight > owned_capacity:
                break
            weight += candidate_weight
            end += 1
            if weight >= owned_capacity:
                break
        ranges.append((start, end))
        start = end
    return ranges


def _validate_chunk_against_source(chunk: TextChunk, text: str, index: int) -> None:
    if not isinstance(chunk, TextChunk):
        raise TypeError(f"chunk_outputs[{index}] chunk must be a TextChunk")
    if chunk.end_offset > len(text):
        raise ValueError(f"chunk_outputs[{index}] extends beyond the source text")
    if chunk.text != text[chunk.begin_offset:chunk.end_offset]:
        raise ValueError(f"chunk_outputs[{index}] text does not match the source text")


def _validate_integer(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
