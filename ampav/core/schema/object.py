from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import Segment
from enum import StrEnum, auto
from .image import Image, BoundingBox


class DetectedObject(Segment, BoundingBox):
    image: Image | None = Field(None, description="Image of the object")
    text: str | None = Field(None, description="text name of the object")
    label: str | None = Field(None, description="Tool-specific label name")
    


class DetectedObjects(AmpAVBaseModel):
    ampav_format: Literal['detected_objects/1'] = 'detected_objects/1'    
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    objects: list[DetectedObject] = Field(default_factory=list, description="Objects detected in the video")

