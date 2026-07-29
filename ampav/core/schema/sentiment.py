from pydantic import Field
from typing import Any, Literal
from .basemodel import AmpAVBaseModel
from .segments import Segment
from enum import StrEnum, auto

class SentimentType(StrEnum):
    """Generic classification of sentiment"""
    POSITIVE = auto()
    "Positive Sentiment"
    NEUTRAL = auto()
    "Neutral Sentiment"
    NEGATIVE = auto()
    "Negative Sentiment"
    UNKNOWN = auto()
    "Sentiment is unset"
    

class Sentiment(AmpAVBaseModel):
    """Sentiment for a segment of media """
    type: SentimentType = SentimentType.UNKNOWN
    "Sentiment for these instances"
    label: str | None = None
    "Sentiment label"
    instances: list[Segment] = Field(default_factory=list)
    "Where this sentiment is found"
    tool_private: dict[str, Any] | None = None
    "Tool-specific data"


class Sentiments(AmpAVBaseModel):
    """A collection of sentiments found in the media"""
    ampav_format: Literal['sentiments/1'] = 'sentiments/1'
    media_duration: float | None = None
    "Duration of the media, if known"
    sentiments: list[Sentiment] = Field(default_factory=list)
    "The sentiments found in the media"

