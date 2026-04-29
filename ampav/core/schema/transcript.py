from pydantic import Field
from typing import Callable, Literal, Annotated, Union, Any
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

    def remove_overlapping_words(self, tiebreaker: Callable | None=None,
                                 paragraph_gap: float = 1.5, 
                                 max_paragraph: float=10, 
                                 separator: str=''):
        self.words = remove_overlapping_words(self.words, tiebreaker)
        # at this point the paragraphs and the text is invalid, so let's fix
        # that too
        self.reformat_paragraphs(paragraph_gap, max_paragraph)
        self.text = separator.join(x.to_str() for x in self.words)



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


def remove_overlapping_words(words: list[WordSegment], tiebreaker: Callable=None) -> list[WordSegment]:
    """Given a list of word segments where some of the words 
       overlap, remove the overlapping ones.  Optionally, a tiebreaker function
       can be used to break ties"""
    if tiebreaker is None:
        # do nothing
        tiebreaker = lambda x: 1

    def overlap(w1: WordSegment, w2: WordSegment):
        return (w2.start_time <= w1.start_time <= w2.end_time) or (w2.start_time <= w1.end_time <= w2.end_time)
            
    new_words: list[WordSegment] = []
    last_end = 0
    while words:
        w = words.pop(0)
        if w.start_time >= last_end:
            new_words.append(w)
            last_end = w.end_time
        else:
            # we have to back up from new words.
            #print(f"OVERLAP: {last_end}: {w}")            
            backtrack = []
            #while new_words and new_words[-1].end_time > w.start_time:
            #    if overlap(w, new_words[-1]):
            #        print(f"OVERLAPPING WORDS: {w}, {new_words[-1]}")
            #    backtrack.append(new_words.pop())
            while new_words and not overlap(w, new_words[-1]):
                backtrack.append(new_words.pop())
            #print("WORDS:\n", "\n".join([str(x) for x in new_words[:-20]]))
            #print("BACKTRACK:\n", "\n".join([str(x) for x in backtrack]))
            #print("LOOKAHEAD:\n", "\n".join([str(x) for x in words[0:len(backtrack)]]))
            while backtrack and words:
                bt = backtrack.pop()
                la = words.pop(0)
                if tiebreaker(bt) > tiebreaker(la):
                    new_words.append(bt)
                    last_end = bt.end_time
                else:
                    new_words.append(la)
                    last_end = la.end_time
            if backtrack:
                new_words.extend(backtrack)

    return new_words