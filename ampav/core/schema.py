from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any

class ToolInformation(BaseModel):
    name: str
    version: str
    parameters: dict[str, Any] = Field(default_factory=dict, 
                                       description="Tool parameters")
    queue_time: float | None = Field(default=None, description="Time the job was queued (if any)")
    start_time: float | None = Field(default=None, description="Time the job started")
    end_time: float | None = Field(default=None, description="Time the job ended")
    log: list[str] = Field(default_factory=list, description="Log data for the job")
    
    def duration(self):
        if None in (self.start_time, self.end_time):
            return None
        return self.end_time - self.start_time


class ErrorOutput(BaseModel):
    output_type: Literal['error'] = 'error'
    message: str = Field(default="An error occurred",
                         description="Error output from the tool")
    details: str = "No details"


class WordData(BaseModel):
    word: str = Field(description="Word")
    start: float | None= Field(default=None, description="Start time of the word")
    end: float | None = Field(default=None, description="End time of the word")
    tool_specific: dict[str, Any] | None = Field(default=None, description="Additional data provided by the tool")
        

class TranscriptOutput(BaseModel):
    output_type: Literal['transcript'] = 'transcript'
    text: str = Field(default="", description="Raw text output of the transcription")
            
    words: list[WordData] = Field(default_factory=list, 
                                  description="Timestamped words in the transcript")
    
    def text_from_words(self):
        """Populate the text field from the timestamped words.  We should only
           need to do this if the tool itself doesn't provide a raw text output        
        """
        self.text = " ".join([w.word for w in self.words])


    def words_from_text(self):
        """Populate the words field from the raw text transcript.  We should only
        need to do this if the tool itself doesn't provide a separate word list.
        Note that this doesn't create any timestamps"""
        self.words = [WordData(word=x) for x in self.text.split()]

    
class LanguageDetectionOutput(BaseModel):
    output_type: Literal['languages'] = 'languages'


ToolOutput = Annotated[Union[LanguageDetectionOutput, TranscriptOutput, ErrorOutput],
                       Field(discriminator='output_type')]


class Metadata(BaseModel):
    metadata_version: Literal['0.0.1'] = '0.0.1'
    info: ToolInformation = Field(default_factory=ToolInformation,
                                  description="Tool Information")
    output: None | ToolOutput = Field(default=None, description="Tool Output")



