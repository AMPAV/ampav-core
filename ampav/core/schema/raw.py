from pydantic import Field
from typing import Callable, Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel


class RawData(AmpAVBaseModel):
    """Tool output that is just data"""
    ampav_format: Literal['raw/1'] = 'raw/1'
    data_type: str | None = Field(None, description="data type name")
    data: Any | None = Field(None, description="Raw Data Structure")


class RawBinary(AmpAVBaseModel):
    """Binary Tool Output"""
    ampav_format: Literal['binary/1'] = 'binary/1'
    data_type: str | None = Field(None, description="data type name")
    data: bytes = Field(default_fatory=bytes, description="Raw binary data")
    