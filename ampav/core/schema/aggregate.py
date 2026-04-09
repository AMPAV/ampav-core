from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
from pathlib import Path
from .basemodel import AmpAVBaseModel
from .av_metadata import AVMetadata


class AmpAVAggregate(AmpAVBaseModel):
    version: Literal[1] = 1
    filename: str
    technical: AVMetadata 
    tool_output: dict[str, Any]

    @staticmethod
    def create_from_file(file: Path) -> "AmpAVAggregate":
        """Create an empty AmpAV data structure from an input file"""
        ampav = AmpAVAggregate(version='1',
                      filename=str(file),
                      technical=AVMetadata.from_file(file))
        return ampav

    