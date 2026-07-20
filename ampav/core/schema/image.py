import base64

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import Segment
from enum import StrEnum, auto
import PIL.Image
import io


# 
# Create a custom data type for storing images inline
#
def validate_pil_image(v: Any) -> PIL.Image.Image:
    if isinstance(v, PIL.Image.Image):
        return v
    if isinstance(v, bytes):
        return PIL.Image.open(io.BytesIO(v))
    if isinstance(v, str) and v.startswith('data:image/png;base64,'):
        # this is a base64-encoded image
        v = base64.b64decode(v[22:])
        return PIL.Image.open(io.BytesIO(v))

    raise ValueError("Input must be PIL image or bytes")


def serialize_pil_image(img: PIL.Image.Image):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return "data:image/png;base64," + img_str


SerializableImage = Annotated[PIL.Image.Image, 
                          BeforeValidator(validate_pil_image),
                          PlainSerializer(serialize_pil_image, return_type=str)]


class Image(AmpAVBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ampav_format: Literal['image/1'] = 'image/1'
    filename: str | None = Field(None, description="Filename")


class BoundingBox(AmpAVBaseModel):
    """A stereotypical bounding box"""
    x1: int = Field(None, help="Upper left corner X")
    y1: int = Field(None, help="Upper left corner Y")
    x2: int = Field(None, help="Lower right corner X")
    y2: int = Field(None, help="Lower right corner Y")

    @property
    def width(self):
        return abs(self.x2 - self.x1)
    

    @property
    def height(self):
        return abs(self.y2 - self.y1)
    

class OcrRegion(BoundingBox):
    """ A region of OCR Text """
    angle: float = Field(0.0, description="Text Angle")
    text: str | None = Field(None, description="OCR Text")
    language: str | None = Field(None, description="Language used")
