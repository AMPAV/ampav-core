from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel


class Segment(AmpAVBaseModel):
    """Base class for a time-based segment"""
    start_time: float | None= Field(None, description="Start time of the segment")
    end_time: float | None = Field(None, description="End time of the segment")
    confidence: float | None = Field(None, description="Confidence score, normalized to 0-1")
    tool_private: dict[str, Any] | None = Field(None, description="Private data provided by the tool")

    def duration(self) -> float:
        """
        Return the duration of the segment
        
        :return: duration of the segment
        :rtype: float
        """
        if self.start_time is not None and self.end_time is not None:
            return self.end_time  - self.start_time
        else:
            return 0


class WordSegment(Segment):
    """Segment representing a word"""
    speaker: str | None = Field(None, description="Speaker of the word")
    prefix: str | None = Field(None, description="Punctuation/whitespace word prefix from transcriber")
    word: str = Field(description="Word text")
    suffix: str | None = Field(None, description="Punctuation/whitespace word suffix from transcriber")
    language: str | None = Field(None, description="Word language")
        
    @staticmethod
    def from_str(word: str, **kwargs) -> "WordSegment":
        """
        Remove prefix/suffix from a word and return a segment
        :param word: the raw word
        :type word: str
        :param kwargs: segment-compatible kwargs
        :return: a new word segment
        :rtype: WordSegment
        """
        ixes = (''' ,.?![]()'"{}<>;:''')
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
                ('' if self.suffix is None else self.suffix))
    

class ParagraphSegment(Segment):
    """Representation of a paragraph segment"""
    speaker: str | None = Field(None, description="Speaker of the paragraph")
    text: str | None = Field(None, description="Paragraph text")
    language: str | None = Field(None, description="Language used in paragraph")
    





