from pydantic import Field
from typing import Literal
from .basemodel import AmpAVBaseModel
from .segments import Segment
from .image import Image, BoundingBox


class DetectedObject(Segment, BoundingBox):
    image: Image | None = Field(None, description="Image of the object")
    text: str | None = Field(None, description="text name of the object")
    label: str | None = Field(None, description="Tool-specific label name")
    


class DetectedObjects(AmpAVBaseModel):
    """A collection of objects detected in the media"""
    ampav_format: Literal['detected_objects/1'] = 'detected_objects/1'    
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    objects: list[DetectedObject] = Field(default_factory=list, description="Objects detected in the video")

