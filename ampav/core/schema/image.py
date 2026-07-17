from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
from .basemodel import AmpAVBaseModel
from .segments import Segment
from enum import StrEnum, auto
import PIL.Image
import io


class Image(AmpAVBaseModel):
    ampav_format: Literal['image/1'] = 'image/1'
    filename: str | None = Field(None, description="Filename")
    width: int | None = Field(None, description="width")
    height: int | None = Field(None, description="height")
    data: bytes | None = Field(None, description="raw image data")

    def get_image(self) -> PIL.Image.Image:
        """ Convert the data into a PIL Image """
        image = PIL.Image.open(io.BytesIO(self.data))
        if self.filename is None:
            self.filename = image.filename
        if self.width is None:
            self.width = image.width
        if self.height is None:
            self.height = image.height
        return image
            

    def set_image(self, image: PIL.Image.Image,
                  filename: str, format: str | None=None,
                  **kwargs):
        """ Store the given PIL Image into the object.  The parameters are
            the same as Image.save()"""
        self.width = image.width
        self.height = image.height
        self.filename = filename        
        tmp = io.BytesIO()
        image.save(tmp, format, **kwargs)
        self.data = tmp.getvalue()



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