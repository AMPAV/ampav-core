import unittest

from pydantic import ValidationError

from ampav.core.schema import NamedEntities, NamedEntity, NamedEntityType, ToolOutput
from ampav.core.schema.compound import CompoundOutput


class TestNamedEntitySchema(unittest.TestCase):
    def test_named_entity_preserves_specific_label_with_broad_type(self):
        entity = NamedEntity(
            text="Kindle",
            type=NamedEntityType.BRAND,
            label="COMMERCIAL_ITEM",
        )

        self.assertEqual(entity.type, "brand")
        self.assertEqual(entity.label, "COMMERCIAL_ITEM")

    def test_tool_output_accepts_named_entities(self):
        output = ToolOutput(
            tool_name="aws_comprehend",
            output={
                "ampav_format": "named_entities/1",
                "text": "AWS Comprehend detected Amazon in Seattle.",
                "spans": [
                    {
                        "text": "Amazon",
                        "label": "ORGANIZATION",
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
        self.assertEqual(output.output.spans[0].label, "ORGANIZATION")

    def test_compound_output_accepts_named_entities(self):
        output = CompoundOutput(
            outputs={
                "named_entities": NamedEntities(
                    text="AWS Comprehend detected Seattle.",
                    spans=[
                        NamedEntity(
                            text="Seattle",
                            label="LOCATION",
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
                label="ORGANIZATION",
                begin_offset=30,
                end_offset=24,
            )


if __name__ == "__main__":
    unittest.main()
