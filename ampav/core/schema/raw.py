import base64
import io

from pydantic import BeforeValidator, Field, PlainSerializer
from typing import Callable, Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel


class RawData(AmpAVBaseModel):
    """Tool output that is just data"""
    ampav_format: Literal['raw/1'] = 'raw/1'
    data_type: str | None = Field(None, description="data type name")
    data: Any | None = Field(None, description="Raw Data Structure")




# 
# Create a custom data type for storing binary data
#
def validate_raw_binary(v: Any) -> bytes:
    if isinstance(v, bytes):
        return v
    if isinstance(v, str):
        # this is base64-encoded data
        return base64.b64decode(v)

    raise ValueError("Input must be base64 string or bytes")


def serialize_raw_binary(data: bytes):
    return base64.b64encode(data).decode('utf-8')


SerializableBinary = Annotated[bytes, 
                               BeforeValidator(validate_raw_binary),
                               PlainSerializer(serialize_raw_binary, return_type=str)]



class RawBinary(AmpAVBaseModel):
    """Binary Tool Output"""
    ampav_format: Literal['binary/1'] = 'binary/1'
    data_type: str | None = Field(None, description="data type name")
    data: SerializableBinary | None = Field(None, description="Raw binary data")
    