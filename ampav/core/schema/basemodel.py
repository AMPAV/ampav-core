from pydantic import BaseModel, ConfigDict
import yaml


class AmpAVBaseModel(BaseModel):
    """Add common features needed for all of the AMPAV models"""
    
    # Behavioral changes for pydantic:
    # * if we have an enum class, render it as the value when serializing
    # * use the docstrings on attributes rather than using just the
    #   description field so it shows up both in the generated documentation
    #   and in visual studio code
    model_config = ConfigDict(use_enum_values=True,
                              use_attribute_docstrings=True)
    
    
    def model_dump_yaml(self, **kwargs) -> str:
        """Dump the model as a yaml string"""
        return yaml.safe_dump(self.model_dump(exclude_none=True), **kwargs)
