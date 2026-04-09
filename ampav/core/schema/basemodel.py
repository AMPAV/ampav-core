from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any
import yaml


class AmpAVBaseModel(BaseModel):
    """Add a YAML dumper to the models"""
    def model_dump_yaml(self, **kwargs):
        return yaml.safe_dump(self.model_dump(exclude_none=True), **kwargs)