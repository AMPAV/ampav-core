from pydantic import Field
from typing import Literal
from .basemodel import AmpAVBaseModel
from .segments import Segment
from enum import StrEnum, auto

class SentimentType(StrEnum):
    """Generic classification of sentiment"""
    POSITIVE = auto()
    NEUTRAL = auto()
    NEGATIVE = auto()
    UNKNOWN = auto()
    

class Sentiment(Segment):
    """Sentiment for a segment of media
       """
    type: SentimentType = Field(SentimentType.UNKNOWN, descriptions="Sentiment for this range")
    label: str | None = Field(None, description="Sentiment label")    


class Sentiments(AmpAVBaseModel):
    """A collection of sentiments found in the media"""
    ampav_format: Literal['sentiments/1'] = 'sentiments/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    sentiments: list[Sentiment] = Field(default_factory=list, description="The sentiments in the media")

    