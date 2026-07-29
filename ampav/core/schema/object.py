from enum import StrEnum, auto

from pydantic import Field
from typing import Any, Literal
from .basemodel import AmpAVBaseModel
from .segments import ConfidenceSegment, Segment
from .image import Image, BoundingBox

class DetectedObjectType(StrEnum):
    OBJECT=auto()
    "An object"
    FACE=auto()
    "A Face"
    OTHER=auto()
    "Something that doesn't fit the above categories"
    UNKNOWN=auto()
    "Unknown or unset"



class DetectedObjectInstance(ConfidenceSegment):
    images: list[Image] = Field(default_factory=list)
    "Images found in the segment"


class DetectedObject(AmpAVBaseModel):
    type: DetectedObjectType = DetectedObjectType.UNKNOWN
    "Type of detected object"
    image: Image | None =None
    "Typical Image of the object"
    text: str | None = None
    "text name of the object"
    label: str | None = None
    "Tool-specific label name"
    instances: list[DetectedObjectInstance] = Field(default_factory=list)
    "Instances where the object appears"
    tool_private: dict[str, Any] | None = None
    "Additional tool-specific fields"


class DetectedObjects(AmpAVBaseModel):
    """A collection of objects detected in the media"""
    ampav_format: Literal['detected_objects/1'] = 'detected_objects/1'    
    media_duration: float | None = None
    "Duration of the media, if known"
    objects: list[DetectedObject] = Field(default_factory=list)
    "Objects detected in the video"

