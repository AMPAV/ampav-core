import unittest

from ampav.core.schema import NamedEntity, TextSpan, WordSegment
from ampav.core.text_chunking import (
    TextChunk,
    TextUnit,
    chunk_text,
    dechunk_text_spans,
    text_to_units,
    words_to_text_units,
)


class TextUnitBuilderTest(unittest.TestCase):
    def test_text_to_units_preserves_source_with_whitespace_and_unicode(self) -> None:
        text = "  Maya  東京.\n"

        units = text_to_units(text)

        self.assertEqual(
            [text[unit.begin_offset:unit.end_offset] for unit in units],
            ["  Maya  ", "東京.\n"],
        )
        self.assertEqual([unit.weight for unit in units], [1, 1])

    def test_text_to_units_supports_custom_utf8_weight(self) -> None:
        text = "Maya 東京"

        units = text_to_units(text, weight_fn=lambda value: len(value.encode("utf-8")))

        self.assertEqual([unit.weight for unit in units], [5, 6])

    def test_text_to_units_handles_empty_and_whitespace_only_text(self) -> None:
        self.assertEqual(text_to_units(""), [])
        self.assertEqual(text_to_units("   "), [TextUnit(0, 3)])

    def test_words_to_text_units_builds_canonical_text_and_ranges(self) -> None:
        words = [
            WordSegment(word="Maya"),
            WordSegment(prefix="(", word="Chen", suffix=")"),
        ]

        text, units = words_to_text_units(words, separator=" | ")

        self.assertEqual(text, "Maya | (Chen)")
        self.assertEqual(
            [text[unit.begin_offset:unit.end_offset] for unit in units],
            ["Maya | ", "(Chen)"],
        )

    def test_words_to_text_units_applies_weight_to_rendered_unit(self) -> None:
        words = [WordSegment(word="IU", suffix="'s"), WordSegment(word="Media")]

        text, units = words_to_text_units(words, weight_fn=lambda value: 2 if "IU's" in value else 1)

        self.assertEqual(text, "IU's Media")
        self.assertEqual([unit.weight for unit in units], [2, 1])

    def test_unit_builders_reject_invalid_weights_and_empty_words(self) -> None:
        with self.assertRaises(ValueError):
            text_to_units("Maya", weight_fn=lambda _: 0)
        with self.assertRaises(TypeError):
            text_to_units("Maya", weight_fn=lambda _: 1.5)
        with self.assertRaises(ValueError):
            words_to_text_units([WordSegment(word="")])


class ChunkTextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = "one two three four"
        self.units = text_to_units(self.text)

    def test_text_that_fits_returns_one_chunk(self) -> None:
        chunks = chunk_text(self.text, self.units, max_weight=4)

        self.assertEqual(
            chunks,
            [TextChunk(self.text, 0, len(self.text), 0, len(self.text))],
        )

    def test_chunk_text_without_overlap_partitions_source(self) -> None:
        chunks = chunk_text(self.text, self.units, max_weight=2)

        self.assertEqual([chunk.text for chunk in chunks], ["one two ", "three four"])
        self.assertEqual(
            [(chunk.owned_begin_offset, chunk.owned_end_offset) for chunk in chunks],
            [(0, 8), (8, 18)],
        )

    def test_chunk_text_adds_context_and_keeps_owned_ranges_disjoint(self) -> None:
        chunks = chunk_text(self.text, self.units, max_weight=3, overlap_weight=1)

        self.assertEqual(
            [chunk.text for chunk in chunks],
            ["one two ", "one two three ", "two three four", "three four"],
        )
        self.assertEqual(
            [(chunk.owned_begin_offset, chunk.owned_end_offset) for chunk in chunks],
            [(0, 4), (4, 8), (8, 14), (14, 18)],
        )

    def test_chunk_text_honors_weighted_units(self) -> None:
        units = text_to_units(self.text, weight_fn=lambda value: 2 if value.startswith("two") else 1)

        chunks = chunk_text(self.text, units, max_weight=3)

        self.assertEqual([chunk.text for chunk in chunks], ["one two ", "three four"])

    def test_chunk_text_rejects_invalid_units_and_limits(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text(self.text, self.units, max_weight=2, overlap_weight=1)
        with self.assertRaises(ValueError):
            chunk_text(self.text, [], max_weight=4)
        with self.assertRaises(ValueError):
            chunk_text(self.text, [TextUnit(1, len(self.text))], max_weight=2)
        with self.assertRaises(ValueError):
            chunk_text(
                self.text,
                [TextUnit(0, 8), TextUnit(7, len(self.text))],
                max_weight=2,
            )
        with self.assertRaises(ValueError):
            chunk_text(self.text, [TextUnit(0, len(self.text) + 1)], max_weight=2)
        with self.assertRaises(ValueError):
            chunk_text(self.text, [TextUnit(0, len(self.text), 3)], max_weight=2)
        with self.assertRaises(ValueError):
            chunk_text(self.text, self.units[:-1], max_weight=4)


class DechunkTextSpansTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = "one two three four"
        self.chunks = chunk_text(
            self.text,
            text_to_units(self.text),
            max_weight=3,
            overlap_weight=1,
        )

    def test_dechunk_rebases_and_filters_overlap_results(self) -> None:
        chunk_outputs = [
            (self.chunks[0], [NamedEntity(text="two", label="NUMBER", begin_offset=4, end_offset=7)]),
            (self.chunks[1], [NamedEntity(text="two", label="NUMBER", begin_offset=4, end_offset=7)]),
            (self.chunks[2], [NamedEntity(text="three", label="NUMBER", begin_offset=4, end_offset=9)]),
            (self.chunks[3], []),
        ]

        spans = dechunk_text_spans(self.text, chunk_outputs)

        self.assertEqual(
            [(span.text, span.begin_offset, span.end_offset) for span in spans],
            [("two", 4, 7), ("three", 8, 13)],
        )

    def test_dechunk_assigns_boundary_crossing_entity_by_midpoint(self) -> None:
        chunk_outputs = [
            (self.chunks[0], []),
            (self.chunks[1], [TextSpan(text="two three", begin_offset=4, end_offset=13)]),
            (self.chunks[2], [TextSpan(text="two three", begin_offset=0, end_offset=9)]),
            (self.chunks[3], []),
        ]

        spans = dechunk_text_spans(self.text, chunk_outputs)

        self.assertEqual(len(spans), 1)
        self.assertEqual(
            (spans[0].text, spans[0].begin_offset, spans[0].end_offset),
            ("two three", 4, 13),
        )

    def test_dechunk_sorts_results_by_original_offsets(self) -> None:
        chunk = chunk_text(self.text, text_to_units(self.text), max_weight=4)[0]
        chunk_outputs = [
            (
                chunk,
                [
                    TextSpan(text="three", begin_offset=8, end_offset=13),
                    TextSpan(text="two", begin_offset=4, end_offset=7),
                ],
            )
        ]

        spans = dechunk_text_spans(self.text, chunk_outputs)

        self.assertEqual([span.text for span in spans], ["two", "three"])

    def test_dechunk_preserves_subclass_fields_without_mutating_input(self) -> None:
        entity = NamedEntity(
            text="three",
            label="NUMBER",
            confidence=0.9,
            begin_offset=4,
            end_offset=9,
            tool_private={"native": True},
        )
        chunk_outputs = [
            (self.chunks[0], []),
            (self.chunks[1], []),
            (self.chunks[2], [entity]),
            (self.chunks[3], []),
        ]

        spans = dechunk_text_spans(self.text, chunk_outputs)

        self.assertIsInstance(spans[0], NamedEntity)
        self.assertEqual(spans[0].label, "NUMBER")
        self.assertEqual(spans[0].tool_private, {"native": True})
        self.assertEqual((entity.begin_offset, entity.end_offset), (4, 9))
        self.assertIsNot(spans[0], entity)

    def test_dechunk_rejects_missing_offsets_and_text_mismatch(self) -> None:
        empty_outputs = [(chunk, []) for chunk in self.chunks]
        with self.assertRaises(ValueError):
            dechunk_text_spans(
                self.text,
                [(self.chunks[0], [TextSpan(text="one")]), *empty_outputs[1:]],
            )
        with self.assertRaises(ValueError):
            dechunk_text_spans(
                self.text,
                [(self.chunks[0], [TextSpan(text="wrong", begin_offset=0, end_offset=3)]), *empty_outputs[1:]],
            )

    def test_dechunk_rejects_incomplete_owned_coverage(self) -> None:
        with self.assertRaises(ValueError):
            dechunk_text_spans(self.text, [(self.chunks[0], [])])


if __name__ == "__main__":
    unittest.main()
