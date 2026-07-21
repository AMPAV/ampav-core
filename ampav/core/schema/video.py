from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any

from ampav.core.schema.image import Image, OcrRegion
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
    type: VideoPatternType = Field(VideoPatternType.UNKNOWN, description="The video pattern type")
    label: str | None = Field(None, description="The label for the video pattern")
    


class VideoPatterns(AmpAVBaseModel):
    """A collection of video patterns found in the media"""
    ampav_format: Literal['video_patterns/1'] = 'video_patterns/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    patterns: list[VideoPattern] = Field(default_factory=list, description="The video patterns in the media")

    
class VideoOcrResult(Segment, OcrRegion):
    """OCR Text Result"""
    # Segment Gives us confidence and tool_private
    # OcrRegion gives us Bounding box and angle, text, language
    pass


class VideoOcr(AmpAVBaseModel):
    """A collection of OCR results for the media"""
    ampav_format: Literal['video_ocr/1'] = 'video_ocr/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    ocr: list[VideoOcrResult] = Field(default_factory=list, description="Everywhere OCR is found")


class VideoSegmentType(StrEnum):
    """The different types of video segments"""
    SHOT = auto()
    SCENE = auto()
    UNKNOWN = auto()


class KeyFrame(AmpAVBaseModel):
    """A keyframe image with timestamp"""
    time: float | None = Field(None, description="Time when frame appears")
    frame: Image | None = Field(None, description="Key Frame Image")


class VideoSegment(Segment):
    """A video segment"""
    type: VideoSegmentType = Field(VideoSegmentType.UNKNOWN, description="Type of segment")
    label: str | None = Field(None, description="Label for the segment")
    keyframes: list[KeyFrame] = Field(default_factory=list, description="Key frames associated with the segment")


class VideoSegments(AmpAVBaseModel):
    """A collection of video segments for the media"""
    ampav_format: Literal['video_segments/1'] = 'video_segments/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")    
    segments: list[VideoSegment] = Field(default_factory=list, description="Segments")