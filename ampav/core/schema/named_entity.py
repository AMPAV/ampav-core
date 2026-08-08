from enum import StrEnum, auto

from pydantic import Field
from typing import Literal

from .text_span import TextSpan, TextSpans


class NamedEntityType(StrEnum):
    """The generic type of the named entity
    
    Note: This initial list is based on AWS Comprehend's types
    from https://docs.aws.amazon.com/comprehend/latest/dg/how-entities.html
    """
    COMMERCIAL_ITEM = auto()
    DATE = auto()
    EVENT = auto()
    LOCATION = auto()
    ORGANIZATION = auto()    
    OTHER = auto()
    PERSON = auto()
    QUANTITY = auto()
    TITLE = auto()
    UNKNOWN = auto()

    BRAND = auto()


class NamedEntity(TextSpan):
    """Named entity mention found in source text."""
    type: NamedEntityType = NamedEntityType.UNKNOWN
    "Named Entity Type"
    label: str 
    "The raw label from the tool"


class NamedEntities(TextSpans):
    """Named entities extracted from source text."""
    ampav_format: Literal["named_entities/1"] = "named_entities/1"
    spans: list[NamedEntity] = Field(default_factory=list)
    "Named entities found in the source text"


