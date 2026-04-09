from pydantic import Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import TimedWordSegment, TimedParagraphSegment



class Transcript(AmpAVBaseModel):
    ampav_format: Literal['transcript'] = 'transcript'
    ampav_format_version: Literal[1] = 1

    text: str = Field(default="", description="Raw text output of the transcription")
            
    words: list[TimedWordSegment] = Field(default_factory=list, 
                                  description="Timestamped words in the transcript")
    paragraphs: list[TimedParagraphSegment] = Field(default_factory=list,
                                                    description="Timestamped paragraphs")




