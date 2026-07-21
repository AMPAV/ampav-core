from enum import StrEnum, auto
from pydantic import Field
from typing import Literal
from ampav.core.schema.basemodel import AmpAVBaseModel
from ampav.core.schema.segments import Segment


class AnnotationType(StrEnum):
    """Type of annotation"""
    KEYWORD = auto()
    LABEL = auto()
    TOPIC = auto()

    OTHER = auto()
    UNKNOWN = auto()


class Annotation(Segment):
    """Annotation Entry"""
    type: AnnotationType = Field(AnnotationType.UNKNOWN, description="Annontation Type")
    text: str | None = Field(None, description="Annotation text")
    

class Annotations(AmpAVBaseModel):
    """Annotations for the given media."""
    ampav_format: Literal["annotations/1"] = "annotations/1"
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    annotations: list[Annotation] = Field(default_factory=list, description="Media Annotations")




