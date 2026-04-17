from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel


class Segment(AmpAVBaseModel):
    ampav_format: Literal['timesegment'] = 'segment'
    ampav_format_version: Literal[1] = 1
    start_time: float | None= Field(None, description="Start time of the word")
    end_time: float | None = Field(None, description="End time of the word")
    tool_specific: dict[str, Any] | None = Field(None, description="Additional data provided by the tool")

    def duration(self):
        if self.start_time is not None and self.end_time is not None:
            return self.end_time  - self.start_time
        else:
            return 0


class WordSegment(Segment):
    ampav_format: Literal['wordsegment'] = 'wordsegment'
    speaker: str | None = Field(None, description="Speaker of the word")
    prefix: str | None = Field(None, description="Word prefix data")
    word: str = Field(description="Word")
    suffix: str | None = Field(None, description="Word suffix data")
        
    @staticmethod
    def from_str(word: str, **kwargs) -> "WordSegment":
        ixes = (''' ,.?![](){}<>;:''')
        if word[0] in ixes:
            prefix = word[0]
            word = word[1:]
        else:
            prefix = None
        if word[-1] in ixes:
            suffix = word[-1]
            word = word[:-1]
        else:
            suffix = None
        return WordSegment(word=word, prefix=prefix, suffix=suffix, **kwargs)

    def to_str(self) -> str:
        """return the prefix + word + suffix"""
        return (('' if self.prefix is None else self.prefix) + 
                self.word +
                ('' if self.suffix is None else self.suffix)).strip()
    
class ParagraphSegment(Segment):
    ampav_format: Literal['paragraph_segment'] = 'paragraph_segment'
    speaker: str | None = Field(None, description="Speaker of the paragraph")
    text: str | None = Field(None, description="Paragraph text")



SegmentType = Annotated[Union[Segment, WordSegment, ParagraphSegment], Field(discriminator='ampav_format')]


class Segments(AmpAVBaseModel):
    ampav_format: Literal['segments'] = 'segments'
    ampav_format_version: Literal[1] = 1
    tool: str
    tag: str
    segments: list[SegmentType] = Field(default_factory=list,
                                    description="Segments")






