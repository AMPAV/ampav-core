from pydantic import Field
from typing import Callable, Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .av_metadata import AVMetadata
from .transcript import Transcript
from .named_entity import NamedEntities
from .key_phrase import KeyPhrases
from .raw import RawData, RawBinary

OutputTypes = Annotated[Union[AVMetadata, Transcript, 
                              NamedEntities, KeyPhrases, RawData, RawBinary], Field(discriminator='ampav_format')]

class CompoundOutput(AmpAVBaseModel):
    """This is for tools which output multiple data types"""
    ampav_format: Literal['compound/1'] = 'compound/1'
    outputs: dict[str | int, OutputTypes] = Field(default_factory=dict, description="Storage of multiple outputs")

    def find_by_type(self, output_type: object) -> list[str]:    
        """Get the output keys for any object that is the same as
           the output type"""
        return [k for k, v in self.outputs.items() if type(output_type) == type(v)]
    
