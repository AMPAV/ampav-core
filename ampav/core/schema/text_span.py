from pydantic import Field, model_validator
from typing import Self

from .basemodel import AmpAVBaseModel
from .segments import Segment, WordSegment


class TextSpan(Segment):
    """Text span found in source text."""

    text: str = Field(description="Text span recognized in the source text")    
    confidence: float | None = Field(None, ge=0, le=1, description="Confidence score, a value between 0 and 1")
    begin_offset: int | None = Field(None, ge=0, description="Character offset where the text span starts")
    end_offset: int | None = Field(None, ge=0, description="Character offset where the text span ends")
    language: str | None = Field(None, description="Language of the text span")

    @model_validator(mode="after")
    def validate_ranges(self) -> Self:
        if self.begin_offset is not None and self.end_offset is not None and self.end_offset < self.begin_offset:
            raise ValueError("end_offset must be greater than or equal to begin_offset")
        if self.start_time is not None and self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time must be greater than or equal to start_time")
        return self


class TextSpans(AmpAVBaseModel):
    """Text spans extracted from source text."""

    # BDW:  Why is this here?  This data type is exclusively for character data
    # and does not have a temporal component.
    media_duration: float | None = Field(default=None, description="Duration of the source media, if known")
    text: str = Field(default="", description="Source text used for text span detection")
    spans: list[TextSpan] = Field(default_factory=list, description="Text spans found in the source text")
    languages: list[str] | None = Field(None, description="Languages represented in the source text")

    def align_timestamps(self, words: list[WordSegment], *, separator: str = " ") -> list[str]:
        """Align text spans to timestamped transcript words.

        `text` must be the canonical source text used for extraction, and span
        offsets must refer to that text. A word is considered matched when its
        canonical character interval overlaps the span interval:
        `word_begin < span_end and word_end > span_begin`.
        The method leaves spans unchanged when alignment cannot be done
        confidently and returns human-readable messages.
        """
        messages: list[str] = []
        if not self.text:
            return [
                "Text span timestamp alignment skipped: missing source text."
            ]
        word_spans = _word_offsets(words, separator=separator)
        word_text_length = word_spans[-1][1] if word_spans else 0
        if word_text_length != len(self.text):
            return [
                "Text span timestamp alignment skipped: source text length does not match the text built from words."
            ]

        sorted_spans = sorted(
            enumerate(self.spans),
            key=lambda item: (item[1].begin_offset is None, item[1].begin_offset or 0),
        )
        word_index = 0
        for span_index, span in sorted_spans:
            if span.begin_offset is None or span.end_offset is None:
                messages.append(f"Text span {span_index} timestamp alignment skipped: missing offsets.")
                continue
            if span.begin_offset < 0 or span.end_offset > len(self.text) or span.end_offset <= span.begin_offset:
                messages.append(f"Text span {span_index} timestamp alignment skipped: offsets are out of range.")
                continue

            while word_index < len(word_spans) and word_spans[word_index][1] <= span.begin_offset:
                word_index += 1

            overlap_index = word_index
            overlapping_words: list[WordSegment] = []
            while overlap_index < len(word_spans) and word_spans[overlap_index][0] < span.end_offset:
                word_begin, word_end, word = word_spans[overlap_index]
                if word_begin < span.end_offset and word_end > span.begin_offset:
                    overlapping_words.append(word)
                overlap_index += 1

            if not overlapping_words:
                messages.append(f"Text span {span_index} timestamp alignment skipped: no overlapping transcript words.")
                continue

            first_word = overlapping_words[0]
            last_word = overlapping_words[-1]
            if first_word.start_time is None or last_word.end_time is None:
                messages.append(f"Text span {span_index} timestamp alignment skipped: overlapping words lack timings.")
                continue

            span.start_time = first_word.start_time
            span.end_time = last_word.end_time

        return messages


def _word_offsets(words: list[WordSegment], *, separator: str) -> list[tuple[int, int, WordSegment]]:
    word_spans: list[tuple[int, int, WordSegment]] = []
    offset = 0
    for word_index, word in enumerate(words):
        if word_index > 0:
            offset += len(separator)
        begin_offset = offset
        offset += len(word.to_str())
        word_spans.append((begin_offset, offset, word))
    return word_spans
