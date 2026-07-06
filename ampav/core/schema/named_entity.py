from pydantic import Field
from typing import Literal

from .text_span import TextSpan, TextSpans


class NamedEntity(TextSpan):
    """Named entity mention found in source text."""

    entity_type: str = Field(description="Entity category")


class NamedEntities(TextSpans):
    """Named entities extracted from source text."""

    ampav_format: Literal["named_entities/1"] = "named_entities/1"
    spans: list[NamedEntity] = Field(default_factory=list, description="Named entities found in the source text")
