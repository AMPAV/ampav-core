from pydantic import Field
from typing import Callable, Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel

from .av_metadata import AVMetadata
from .transcript import Transcript

OutputTypes = Annotated[Union[AVMetadata, Transcript], Field(discriminator='ampav_format')]

class CompoundOutput(AmpAVBaseModel):
    """This is for tools which output multiple data types"""
    ampav_format: Literal['compound/1'] = 'compound/1'
    outputs: dict[str, OutputTypes] | None = Field(None, description="Storage of multiple outputs")


    def find_by_type(self, output_type: object) -> list[str]:
        """Get the output keys for any object that is the same as
           the output type"""
        return [k for k, v in self.outputs.items() if type(output_type) == type(k)]
    
    