import unittest

from pydantic import ValidationError

from ampav.core.schema import KeyPhrase, KeyPhrases, ToolOutput
from ampav.core.schema.compound import CompoundOutput


class TestKeyPhraseSchema(unittest.TestCase):
    def test_tool_output_accepts_key_phrases(self):
        output = ToolOutput(
            tool_name="aws_comprehend",
            output={
                "ampav_format": "key_phrases/1",
                "text": "AWS Comprehend detected key phrases in Seattle.",
                "spans": [
                    {
                        "text": "key phrases",
                        "confidence": 0.99,
                        "begin_offset": 28,
                        "end_offset": 39,
                    }
                ],
                "languages": ["en"],
            },
        )

        self.assertIsInstance(output.output, KeyPhrases)
        self.assertEqual(output.output.spans[0].text, "key phrases")

    def test_compound_output_accepts_key_phrases(self):
        output = CompoundOutput(
            outputs={
                "key_phrases": KeyPhrases(
                    text="AWS Comprehend detected Seattle.",
                    spans=[
                        KeyPhrase(
                            text="AWS Comprehend",
                            begin_offset=0,
                            end_offset=14,
                        )
                    ],
                )
            }
        )

        self.assertIsInstance(output.outputs["key_phrases"], KeyPhrases)

    def test_key_phrase_rejects_invalid_offsets(self):
        with self.assertRaises(ValidationError):
            KeyPhrase(
                text="key phrases",
                begin_offset=30,
                end_offset=24,
            )


if __name__ == "__main__":
    unittest.main()
