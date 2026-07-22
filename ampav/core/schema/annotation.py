from enum import StrEnum, auto
from pydantic import Field
from typing import Any, Literal
from ampav.core.schema.basemodel import AmpAVBaseModel
from ampav.core.schema.segments import ConfidenceSegment, Segment


class AnnotationType(StrEnum):
    """Types of annotations"""
    KEYWORD = auto()
    "A Keyword annotation"
    LABEL = auto()
    "A label"
    TOPIC = auto()
    "Topic"
    EMOTION=auto()
    "Emotion"
    OTHER = auto()
    "An annotation type where it doesn't fit into any other category"
    UNKNOWN = auto()
    "The annotation has not been typed (yet?)"


class Annotation(AmpAVBaseModel):
    """Annotation Entry"""
    type: AnnotationType = AnnotationType.UNKNOWN
    "The type of annotation"
    text: str | None = None
    "The text associated with the annotation"
    language: str | None = None
    "The language used for the annotation"
    instances: list[ConfidenceSegment] = Field(default_factory=list)
    "The segments where this annotation is observed"
    tool_private: dict[str, Any] | None = None
    "Any addtional tool-native values that are worth storing"


class Annotations(AmpAVBaseModel):
    """Annotations for the given media."""
    ampav_format: Literal["annotations/1"] = "annotations/1"
    media_duration: float | None = None
    "The duration of the media, if known"
    annotations: list[Annotation] = Field(default_factory=list)
    "The annotations for this media"




