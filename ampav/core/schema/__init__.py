from typing import Annotated, Union

from pydantic import Field

from ampav.core.schema.basemodel import AmpAVBaseModel

from .annotation import AnnotationType, Annotation, Annotations
from .audio import AudioEffectType, AudioEffect, AudioEffects
from .av_metadata import AVMetadata
from .compound import CompoundOutput
from .image import Image
from .key_phrase import KeyPhrase, KeyPhrases
from .named_entity import NamedEntityType, NamedEntity, NamedEntities
from .object import DetectedObject, DetectedObjects
from .raw import RawData, RawBinary
from .segments import Segment, WordSegment, ParagraphSegment
from .sentiment import Sentiment, Sentiments, SentimentType
from .text_span import TextSpan, TextSpans
from .tool import ToolOutput
from .transcript import Transcript
from .video import VideoOcrResult, VideoOcr, VideoPatternType, VideoPattern, VideoPatterns, VideoSegmentType, VideoSegment, VideoSegments
from ..utils import load_data
from pathlib import Path


__all__ = [    
    # functions
    "load_ampav_file",
    "parse_ampav_data",

    # Types
    "AnnotationType", 
    "AudioEffectType",
    "NamedEntityType", 
    "SentimentType",
    "VideoPatternType", "VideoSegmentType",

    # Standalone data classes
    "Annotations",
    "AudioEffects",    
    "AVMetadata",
    "CompoundOutput",
    "Image",
    "KeyPhrases",
    "NamedEntities",
    "DetectedObjects",
    "RawData", "RawBinary",
    "Sentiments",
    "ToolOutput",
    "Transcript",
    "VideoOcr", "VideoPatterns", "VideoSegments",    
]


AmpAVDataClass = Annotated[Union["Annotations", "AudioEffects", "AVMetadata",
                                 "CompoundOutput", "Image", "KeyPhrases",
                                 "NamedEntities", "DetectedObjects", "RawData", 
                                 "RawBinary", "ToolOutput", "Transcript",
                                 "VideoOcr", "VideoPatterns", "VideoSegments",
                                 "Sentiments"],
                           Field(discriminator="ampav_format")]


def load_ampav_file(path: Path) -> AmpAVDataClass:
    """Load AMPAV data from the specified path"""
    data = load_data(path)
    return parse_ampav_data(data)


def parse_ampav_data(data: dict) -> AmpAVDataClass:
    """Convert a data structure that represents ampav data into the 
       appropriate python objects"""
    
    # By wrapping this into a bogus class we can make pydantic do all the work 
    # to determine what the content is and create the objects.
    class _FileWrapper(AmpAVBaseModel):
        data: AmpAVDataClass

    return _FileWrapper(data={**data}).data

