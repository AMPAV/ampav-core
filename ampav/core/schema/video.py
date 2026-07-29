from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any

from ampav.core.schema.image import Image, OcrRegion
from .basemodel import AmpAVBaseModel
from .segments import ConfidenceSegment, Segment
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
    CREDITS = auto()
    "Credits"
    OTHER = auto()
    "Other patterns"
    UNKNOWN = auto()
    "Unknown/Unset video pattern"


class VideoPattern(AmpAVBaseModel):
    """Representation of a video pattern segment (color bars, black, etc)       
       """
    type: VideoPatternType = VideoPatternType.UNKNOWN
    "The video pattern type"
    label: str | None = None
    "The label for the video pattern"
    instances: list[ConfidenceSegment] = Field(default_factory=list)
    "Where this video pattern appears in the media"


class VideoPatterns(AmpAVBaseModel):
    """A collection of video patterns found in the media"""
    ampav_format: Literal['video_patterns/1'] = 'video_patterns/1'
    media_duration: float | None = None
    "Duration of the media, if known"
    patterns: list[VideoPattern] = Field(default_factory=list)
    "The video patterns in the media"

    
class VideoOcrResult(ConfidenceSegment, OcrRegion):
    """OCR Text Result"""
    # ConfidenceSegment Gives us confidence
    # OcrRegion gives us Bounding box and angle, text, language
    pass


class VideoOcr(AmpAVBaseModel):
    """A collection of OCR results for the media"""
    ampav_format: Literal['video_ocr/1'] = 'video_ocr/1'
    media_duration: float | None = None
    "Duration of the media, if known"
    ocr: list[VideoOcrResult] = Field(default_factory=list)
    "Everywhere OCR is found"


class VideoSegmentType(StrEnum):
    """The different types of video segments"""
    SHOT = auto()
    SCENE = auto()
    UNKNOWN = auto()


class KeyFrame(AmpAVBaseModel):
    """A keyframe image with timestamp"""
    time: float | None = None
    "Time when frame appears"
    frame: Image | None = None
    "Key Frame Image"


class VideoSegment(Segment):
    """A video segment"""
    type: VideoSegmentType = VideoSegmentType.UNKNOWN
    "Type of segment"
    label: str | None = None
    "Label for the segment"
    keyframes: list[KeyFrame] = Field(default_factory=list)
    "Key frame images for this segment"


class VideoSegments(AmpAVBaseModel):
    """A collection of video segments for the media"""
    ampav_format: Literal['video_segments/1'] = 'video_segments/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")    
    segments: list[VideoSegment] = Field(default_factory=list, description="Segments")