from pydantic import Field
from typing import Literal

#from ampav.core.schema.common import Confidence, TimeSegment
from .basemodel import AmpAVBaseModel
from .segments import ConfidenceSegment, Segment
from enum import StrEnum, auto

class AudioEffectType(StrEnum):
    """Generic classification of the audio effect"""
    SILENCE = auto()
    "Silence"
    MUSIC = auto()
    "Music"
    SPEECH = auto()
    "Speech"
    NOISE = auto()
    "White noise or similar"
    OTHER = auto()
    "Other sound"
    UNKNOWN = auto()
    "Unknown sound"


class AudioEffect(AmpAVBaseModel):
    """Representation of an audio effect (like "silence" or "explosion" or
       whatever).  
       
       For values other than silence, they are included in text output 
       surrounded by square brackets:  "[Gunshot or explosion]"

       The labels should be normalized to lower case
       """
    type: AudioEffectType = AudioEffectType.UNKNOWN
    "Effect type present for these ranges"
    label: str | None = None
    "The label for audio effect"
    instances: list[ConfidenceSegment] = Field(default_factory=list)
    "List of instances for this effect"


class AudioEffects(AmpAVBaseModel):
    """A collection of audio events found in the media"""
    ampav_format: Literal['audio_effects/1'] = 'audio_effects/1'
    media_duration: float | None = None
    "Duration of the media, if known"
    effects: list[AudioEffect] = Field(default_factory=list)
    "The audio effects in the media"


    