import unittest

from pydantic import ValidationError

from ampav.core.schema import KeyPhrase, KeyPhrases, NamedEntity, NamedEntities, TextSpan, Transcript, WordSegment
from ampav.core.schema.transcript import words_to_text


class TestTextSpanSchema(unittest.TestCase):
    def test_text_span_rejects_invalid_timestamp_range(self):
        with self.assertRaises(ValidationError):
            TextSpan(text="bad time", start_time=3.0, end_time=2.0)

    def test_transcript_words_to_text_builds_canonical_text(self):
        transcript = Transcript(
            words=[
                WordSegment(word="Hello", start_time=0.0, end_time=0.4),
                WordSegment(word="world", suffix=".", start_time=0.5, end_time=0.9),
            ]
        )

        self.assertEqual(words_to_text(transcript.words), "Hello world.")

    def test_named_entities_align_timestamps_to_overlapping_words(self):
        words = [
            WordSegment(word="Maya", start_time=1.0, end_time=1.2),
            WordSegment(word="Chen", start_time=1.3, end_time=1.6),
            WordSegment(word="returned", start_time=1.7, end_time=2.1),
            WordSegment(word="Maya", start_time=2.2, end_time=2.5),
            WordSegment(word="Chen", suffix=".", start_time=2.6, end_time=2.9),
        ]
        transcript = Transcript(words=words)
        text = words_to_text(transcript.words)
        output = NamedEntities(
            text=text,
            spans=[
                NamedEntity(text="Maya Chen", entity_type="PERSON", begin_offset=0, end_offset=9),
                NamedEntity(text="Maya Chen", entity_type="PERSON", begin_offset=19, end_offset=28),
            ],
        )

        messages = output.align_timestamps(words)

        self.assertEqual(messages, [])
        self.assertEqual((output.spans[0].start_time, output.spans[0].end_time), (1.0, 1.6))
        self.assertEqual((output.spans[1].start_time, output.spans[1].end_time), (2.2, 2.9))

    def test_key_phrases_align_partial_word_span(self):
        words = [
            WordSegment(word="IU", suffix="'s", start_time=3.0, end_time=3.3),
            WordSegment(word="Media", start_time=3.4, end_time=3.7),
            WordSegment(word="School", start_time=3.8, end_time=4.1),
        ]
        transcript = Transcript(words=words)
        output = KeyPhrases(
            text=words_to_text(transcript.words),
            spans=[KeyPhrase(text="IU", begin_offset=0, end_offset=2)],
        )

        messages = output.align_timestamps(words)

        self.assertEqual(messages, [])
        self.assertEqual((output.spans[0].start_time, output.spans[0].end_time), (3.0, 3.3))

    def test_alignment_returns_message_for_missing_offsets(self):
        words = [WordSegment(word="Amazon", start_time=1.0, end_time=1.5)]
        output = NamedEntities(text="Amazon", spans=[NamedEntity(text="Amazon", entity_type="ORGANIZATION")])

        messages = output.align_timestamps(words)

        self.assertEqual(output.spans[0].start_time, None)
        self.assertEqual(output.spans[0].end_time, None)
        self.assertEqual(messages, ["Text span 0 timestamp alignment skipped: missing offsets."])

    def test_alignment_returns_message_when_source_text_is_missing(self):
        words = [WordSegment(word="Amazon", start_time=1.0, end_time=1.5)]
        output = NamedEntities(
            spans=[NamedEntity(text="Amazon", entity_type="ORGANIZATION", begin_offset=0, end_offset=6)],
        )

        messages = output.align_timestamps(words)

        self.assertEqual(
            messages,
            ["Text span timestamp alignment skipped: missing source text."],
        )

    def test_alignment_returns_message_when_source_text_length_differs(self):
        words = [WordSegment(word="Amazon", start_time=1.0, end_time=1.5)]
        output = NamedEntities(
            text="Different source text",
            spans=[NamedEntity(text="Amazon", entity_type="ORGANIZATION", begin_offset=0, end_offset=6)],
        )

        messages = output.align_timestamps(words)

        self.assertEqual(
            messages,
            ["Text span timestamp alignment skipped: source text length does not match the text built from words."],
        )


if __name__ == "__main__":
    unittest.main()
