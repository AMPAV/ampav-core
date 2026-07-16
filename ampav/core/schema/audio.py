from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import Segment
from enum import StrEnum, auto

class AudioEffectType(StrEnum):
    """Generic classification of the audio effect"""
    SILENCE = auto()
    "Silence"

    MUSIC = auto()
    "Music"

    SPEECH = auto()
    "Speech"

    OTHER = auto()
    "Other Noises"

    UNKNOWN = auto()
    "Unknown Noise"


class AudioEffectSegment(Segment):
    """Representation of an audio effect (like "silence" or "explosion" or
       whatever).  
       
       For values other than silence, they are included in text output 
       surrounded by square brackets:  "[Gunshot or explosion]"

       The values should be normalized to lower case
       """
    effect: AudioEffectType = Field(AudioEffectType.UNKNOWN, descriptions="Effect type present for this range")
    name: str | None = Field(None, description="The name of audio effect")    


class AudioEffects(AmpAVBaseModel):
    ampav_format: Literal['audio_effects/1'] = 'audio_effects/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    effects: list[AudioEffectSegment] = Field(default_factory=list, description="The audio effects in the media")

    def effects_at_point_in_time(self, time_offset: float, min_confidence: float=0) -> set[AudioEffectType]:
        """Return a set of the effects for a given point in time, filtering 
        by minimum confidence"""
        res = set()
        for e in self.effects:
            if e.start_time <= time_offset <= e.end_time and e.confidence >= min_confidence:
                res.add(e)
        return res
    