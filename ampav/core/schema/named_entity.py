from enum import StrEnum, auto

from pydantic import Field
from typing import Literal

from .text_span import TextSpan, TextSpans


class NamedEntityType(StrEnum):
    """Broad, provider-independent category of a named entity.

    The categories are intentionally coarse. Examples in these definitions are
    illustrative rather than exhaustive; a tool's more specific classification
    is retained separately in :attr:`NamedEntity.label`.

    ``BRAND``
        A named commercial identity or offering, including a brand, producer,
        product, service, or other commercially identifiable item.
    ``DATE``
        A date, time, or other expression identifying a temporal point or
        period.
    ``EVENT``
        A named occurrence or activity, such as a ceremony, competition,
        conference, or historical event.
    ``LOCATION``
        A named geographic or physical place, including a country, region,
        city, street, address, building, or venue.
    ``ORGANIZATION``
        A named organized group or institution, including a company, agency,
        school, or association when referenced organizationally.
    ``PERSON``
        A named individual or personal identity.
    ``QUANTITY``
        A stated numeric amount or measurement, including currency,
        percentages, dimensions, and counts.
    ``TITLE``
        The name of a creative work, publication, program, or other titled
        work.
    ``OTHER``
        A recognized entity that does not fit another AMPAV category.
    ``UNKNOWN``
        An entity whose AMPAV category was not determined, such as when a
        native classification is unavailable or has not been mapped.
    """
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
    "Broad AMPAV entity category; UNKNOWN when the category was not determined"
    label: str 
    "The raw, potentially more specific label from the tool"


class NamedEntities(TextSpans):
    """Named entities extracted from source text."""
    ampav_format: Literal["named_entities/1"] = "named_entities/1"
    spans: list[NamedEntity] = Field(default_factory=list)
    "Named entities found in the source text"

