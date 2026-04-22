from pydantic import Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import WordSegment, ParagraphSegment
import logging


class Transcript(AmpAVBaseModel):
    ampav_format: Literal['transcript/1'] = 'transcript/1'
    media_duration: float | None = Field(default=None, description="Duration of the media, if known")
    text: str = Field(default="", description="Raw text output of the transcription")
            
    words: list[WordSegment] = Field(default_factory=list, 
                                  description="Timestamped words in the transcript")
    paragraphs: list[ParagraphSegment] = Field(default_factory=list,
                                                    description="Timestamped paragraphs")


    def reformat_paragraphs(self, paragraph_gap: float=1.5, 
                            max_paragraph: float=10):
        """
        Reformat the paragraphs from the words based on time (if possible)
        otherwise a text estimate
                
        :param paragraph_gap: Time gap to indicate separate paragraphs
        :type paragraph_gap: float
        :param max_paragraph: Maximum paragraph duration
        :type max_paragraph: float
        """
        self.paragraphs = words_to_paragraphs(self.words, paragraph_gap, max_paragraph)



def words_to_paragraphs(words: list[WordSegment], 
                        paragraph_gap: float=1.5,
                        max_paragraph: float=10) -> list[ParagraphSegment]:
    """Convert a list words to a list of paragraphs"""
    # There's two different methods -- if all of the word segments have
    # start and end times, then we'll use paragraph_gap and max_paragraph
    # to determine times.  Otherwise, we'll do a stupid estimation to guess
    # the times.

    paras: list[list[WordSegment]] = []
    if all([x.start_time is not None and x.end_time is not None for x in words]):
        # we have times for everything
        para = []
        para_time = 0
        last_time = words[0].start_time
        for word in words:            
            if word.start_time - last_time > paragraph_gap:
                # new paragraph
                if para:
                    paras.append(para)
                    para = []
                    para_time = 0                    
            para.append(word)
            para_time += word.duration()
            last_time = word.end_time
            
            if para_time >= max_paragraph:
                # start a new paragraph
                paras.append(para)
                para = []
                para_time = 0

        if para:
            paras.append(para)

    else:
        # we're going to make it up as we go
        logging.warning("Not every word has a timestamp so we'll do a text-based split")
        # the average speaker can produce around 20-25 words in 10 seconds, so
        # we'll use the bottom end of things.
        para = []
        for word in words:
            para.append(word)
            if len(para) > 20:
                paras.append(para)
                para = []
        if para:
            paras.append(para)

    # convert the paras array into paragraphs.
    paragraphs = []
    for para in paras:
        p = ParagraphSegment(start_time=para[0].start_time,
                             end_time=para[-1].end_time,
                             speaker=para[0].speaker,
                             text=" ".join([x.to_str() for x in para]))
        paragraphs.append(p)

    return paragraphs