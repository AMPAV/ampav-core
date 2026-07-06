import unittest

from pydantic import ValidationError

from ampav.core.schema import NamedEntities, NamedEntity, ToolOutput
from ampav.core.schema.compound import CompoundOutput


class TestNamedEntitySchema(unittest.TestCase):
    def test_tool_output_accepts_named_entities(self):
        output = ToolOutput(
            tool_name="aws_comprehend",
            output={
                "ampav_format": "named_entities/1",
                "text": "AWS Comprehend detected Amazon in Seattle.",
                "spans": [
                    {
                        "text": "Amazon",
                        "entity_type": "ORGANIZATION",
                        "confidence": 0.99,
                        "begin_offset": 24,
                        "end_offset": 30,
                    }
                ],
                "languages": ["en"],
            },
        )

        self.assertIsInstance(output.output, NamedEntities)
        self.assertEqual(output.output.spans[0].text, "Amazon")
        self.assertEqual(output.output.spans[0].entity_type, "ORGANIZATION")

    def test_compound_output_accepts_named_entities(self):
        output = CompoundOutput(
            outputs={
                "named_entities": NamedEntities(
                    text="AWS Comprehend detected Seattle.",
                    spans=[
                        NamedEntity(
                            text="Seattle",
                            entity_type="LOCATION",
                            begin_offset=24,
                            end_offset=31,
                        )
                    ],
                )
            }
        )

        self.assertIsInstance(output.outputs["named_entities"], NamedEntities)

    def test_named_entity_rejects_invalid_offsets(self):
        with self.assertRaises(ValidationError):
            NamedEntity(
                text="Amazon",
                entity_type="ORGANIZATION",
                begin_offset=30,
                end_offset=24,
            )


if __name__ == "__main__":
    unittest.main()
