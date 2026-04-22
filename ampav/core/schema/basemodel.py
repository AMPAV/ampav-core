from pydantic import BaseModel
import yaml


class AmpAVBaseModel(BaseModel):
    """Add a YAML dumper to the models"""
    def model_dump_yaml(self, **kwargs) -> str:
        """Dump the model as a yaml string"""
        return yaml.safe_dump(self.model_dump(exclude_none=True), **kwargs)