import base64

from pydantic import BeforeValidator, ConfigDict, Field, PlainSerializer
from typing import Literal, Annotated, Any
from .basemodel import AmpAVBaseModel
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
    """An Image"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ampav_format: Literal['image/1'] = 'image/1'
    image: SerializableImage | None = None
    "The image data"
    filename: str | None = None
    "Image Filename, if known"


class BoundingBox(AmpAVBaseModel):
    """A stereotypical bounding box"""
    x: int = 0
    "Upper left corner X"
    y: int = 0
    "Upper left corner y"
    width: int = 0
    "Width of Bounding Box"
    height: int = 0
    "Height of BoundingBox"

    def get_coords(self):
        """return a ((x1, y1), (x2, x2)) tuple of the bounding box corners.
           assumes that the origin is in the upper left."""
        return ((self.x, self.y), (self.x + self.width, self.y + self.height))
        
    def __str__(self):
        "String representation in width x height + x offset + y offset"
        return f"{self.width}x{self.height}+{self.x}+{self.y}"



class OcrRegion(AmpAVBaseModel):
    """ A region of OCR Text """
    bounding_box: BoundingBox
    "Text Bounding box"
    angle: float = 0.0
    "Text Angle"
    text: str | None = None
    "OCR Text"
    language: str | None = None
    "OCR Language"


