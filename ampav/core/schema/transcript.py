from pydantic import Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import WordSegment, ParagraphSegment



class Transcript(AmpAVBaseModel):
    ampav_format: Literal['transcript'] = 'transcript'
    ampav_format_version: Literal[1] = 1

    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    text: str = Field(default="", description="Raw text output of the transcription")
            
    words: list[WordSegment] = Field(default_factory=list, 
                                  description="Timestamped words in the transcript")
    paragraphs: list[ParagraphSegment] = Field(default_factory=list,
                                                    description="Timestamped paragraphs")




