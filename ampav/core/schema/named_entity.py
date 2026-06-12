from pydantic import Field, model_validator
from typing import Literal, Self

from .basemodel import AmpAVBaseModel
from .segments import Segment


class NamedEntity(Segment):
    """Named entity mention found in source text."""

    entity_text: str = Field(description="Text span recognized as an entity")
    entity_type: str = Field(description="Entity category")
    confidence: float | None = Field(None, ge=0, le=1, description="Confidence score, a value between 0 and 1")
    begin_offset: int | None = Field(None, ge=0, description="Character offset where the entity starts")
    end_offset: int | None = Field(None, ge=0, description="Character offset where the entity ends")
    language: str | None = Field(None, description="Language of the entity text")

    @model_validator(mode="after")
    def validate_ranges(self) -> Self:
        if self.begin_offset is not None and self.end_offset is not None and self.end_offset < self.begin_offset:
            raise ValueError("end_offset must be greater than or equal to begin_offset")
        if self.start_time is not None and self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time must be greater than or equal to start_time")
        return self


class NamedEntities(AmpAVBaseModel):
    """Named entities extracted from source text."""

    ampav_format: Literal["named_entities/1"] = "named_entities/1"
    media_duration: float | None = Field(default=None, description="Duration of the source media, if known")
    text: str = Field(default="", description="Source text used for entity detection")
    entities: list[NamedEntity] = Field(default_factory=list, description="Named entities found in the source text")
    languages: list[str] | None = Field(None, description="Languages represented in the source text")
