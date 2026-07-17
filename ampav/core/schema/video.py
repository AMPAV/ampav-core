from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import Segment
from enum import StrEnum, auto

class VideoPatternType(StrEnum):
    """Generic classification of the video pattern"""
    BLACK = auto()
    "Solid black Screen"

    SOLID = auto()
    "Solid color, not black"

    COLORBARS = auto()
    "Color Bars"

    NOISE = auto()
    "Snow or other random signal"

    OTHER = auto()
    "Other patterns"

    UNKNOWN = auto()
    "Unknown video pattern"


class VideoPattern(Segment):
    """Representation of a video pattern segment (color bars, black, etc)       
       """
    pattern: VideoPatternType = Field(VideoPatternType.UNKNOWN, description="The video pattern")
    name: str | None = Field(None, description="The name of the video pattern")
    


class VideoPatterns(AmpAVBaseModel):
    ampav_format: Literal['video_patterns/1'] = 'video_patterns/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    patterns: list[VideoPattern] = Field(default_factory=list, description="The video patterns in the media")

    