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
    languages: list[str] | None = Field(None, description="List of languages in the transcript")


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
                        max_paragraph: float=10,
                        word_count: int=20) -> list[ParagraphSegment]:
    """Convert a list words to a list of paragraphs
    paragraph_gap:  time (in seconds) that delineates a paragraph
    max_paragraph:  longest paragraph allowed in seconds
    word_count:  max number of words to split if we don't have times
    """
    # See if we have timings for everything
    have_timings = all([x.start_time is not None and x.end_time is not None for x in words])

    # Group the words together based on aux information, like
    # speaker and language.  When those things change we're in a new
    # paragraph no matter the timing.
    aux_paras: list[list[WordSegment]] = []
    cur_para = []
    last_aux = (words[0].language, words[0].speaker)
    for w in words:
        aux = (w.language, w.speaker)
        if aux != last_aux and cur_para:
            aux_paras.append(cur_para)
            cur_para = [w]            
        else:
            cur_para.append(w)
        last_aux = aux
    if cur_para:
        aux_paras.append(cur_para)

    def dbg(words: list[WordSegment]):
        return ",".join([f"{word.to_str()}({word.start_time:0.2f},{word.end_time:0.2f})" for word in words])

    # for every aux_paragraph we have to split it into time-based
    # chunks.  If we have timing we'll use the paragraph_gap and
    # max_paragraph to determine where to break it, otherwise we'll use
    # a word count
    paras: list[list[WordSegment]] = []
    for aux_para in aux_paras:
        #print(aux_para[0], '\n  ', aux_para[-1])
        # handle the easiest cases first: it's shorter than our limits.
        if have_timings:
            if aux_para[-1].end_time - aux_para[0].start_time < max_paragraph:                
                paras.append(aux_para)
                continue            
        else:
            if len(aux_para) < word_count:                
                paras.append(aux_para)
                continue

        # Crud, we need to split this paragraph into one or more chunks.
        new_para: list[WordSegment] = []        
        since_last_punc = 0
        i = 0
        while i < len(aux_para):        
            w = aux_para[i]   
            if not new_para:
                print()
            new_para.append(w)         
            if w.suffix is not None and w.suffix.strip() != '':                
                since_last_punc = 0
            else:
                since_last_punc += 1

            if not have_timings:
                if len(new_para) == word_count:                                        
                    if since_last_punc == 0 or len(new_para) == since_last_punc:
                        # we're ending a paragraph here or there isn't any
                        # punctuation to backtrack to.  C'est la vie
                        paras.append(new_para)
                        new_para = []
                        since_last_punc = 0                        
                    else:
                        # we have to back up a bit
                        new_para = new_para[0:-since_last_punc]
                        paras.append(new_para)
                        new_para = []
                        i -= since_last_punc
                        since_last_punc = 0
                        
            else:                
                gap = 0 if len(new_para) < 2 else new_para[-1].start_time - new_para[-2].end_time                
                if len(new_para) > 1 and gap > paragraph_gap:
                    # this word very far away from the previous word                    
                    new_para.pop()
                    i -= 1 # redo the current word                    
                    paras.append(new_para)
                    new_para = []                    
                    since_last_punc = 0
                elif new_para[-1].end_time - new_para[0].start_time > max_paragraph:
                    # our paragraph is too long, theoretically by 1 word...so I'll
                    # let it go.
                    if since_last_punc == 0 or len(new_para) == since_last_punc:
                        # we ended a paragraph or we have nothing to backtrack to                        
                        paras.append(new_para)
                        new_para = []
                        since_last_punc = 0
                    else:
                        # we have to back up a bit                        
                        new_para = new_para[0:-since_last_punc]
                        paras.append(new_para)
                        new_para = []
                        i -= since_last_punc
                        since_last_punc = 0
                else:
                    pass
            i += 1
            
    if new_para:
        paras.append(new_para)

    # convert the paras array into paragraphs.
    paragraphs = []
    for para in paras:
        p = ParagraphSegment(start_time=para[0].start_time,
                             end_time=para[-1].end_time,
                             speaker=para[0].speaker,
                             language=para[0].language,
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
            backtrack = []
            while new_words and not overlap(w, new_words[-1]):
                backtrack.append(new_words.pop())

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