from pydantic import Field
from typing import Any, Literal
from .basemodel import AmpAVBaseModel
from .segments import ConfidenceSegment, Segment
from .image import Image, BoundingBox


class DetectedObject(AmpAVBaseModel):
    image: Image | None =None
    "Image of the object"
    text: str | None = None
    "text name of the object"
    label: str | None = None
    "Tool-specific label name"
    instances: list[ConfidenceSegment] = Field(default_factory=list)
    "Instances where the object appears"
    tool_private: dict[str, Any] = Field(default_factory=dict)
    "Additional tool-specific fields"


class DetectedObjects(AmpAVBaseModel):
    """A collection of objects detected in the media"""
    ampav_format: Literal['detected_objects/1'] = 'detected_objects/1'    
    media_duration: float | None = None
    "Duration of the media, if known"
    objects: list[DetectedObject] = Field(default_factory=list)
    "Objects detected in the video"

