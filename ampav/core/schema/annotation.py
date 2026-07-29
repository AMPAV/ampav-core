from enum import StrEnum, auto
from pydantic import Field
from typing import Any, Literal
from ampav.core.schema.basemodel import AmpAVBaseModel
from ampav.core.schema.segments import ConfidenceSegment, Segment


class AnnotationType(StrEnum):
    """Types of annotations"""
    KEYWORD = auto()
    "A Keyword annotation"
    LABEL = auto()
    "A label"
    TOPIC = auto()
    "Topic"
    EMOTION=auto()
    "Emotion"
    OTHER = auto()
    "An annotation type where it doesn't fit into any other category"
    MATURE = auto()
    "Mature content"
    UNKNOWN = auto()
    "The annotation has not been typed (yet?)"


class Annotation(AmpAVBaseModel):
    """Annotation Entry"""
    type: AnnotationType = AnnotationType.UNKNOWN
    "The type of annotation"
    label: str | None = None
    "The label assigned by the tool"
    text: str | None = None
    "The text associated with the annotation"
    language: str | None = None
    "The language used for the annotation"
    instances: list[ConfidenceSegment] = Field(default_factory=list)
    "The segments where this annotation is observed"
    tool_private: dict[str, Any] | None = None
    "Any addtional tool-native values that are worth storing"

    def can_merge_instances(self, other: "Annotation") -> bool:
        """If this annotation and another one are similar enough that
           they can merge their instances"""
        return ((self.type, self.label, self.text, self.language, self.tool_private) ==
                (other.type, other.label, other.text, other.language, other.tool_private))



class Annotations(AmpAVBaseModel):
    """Annotations for the given media."""
    ampav_format: Literal["annotations/1"] = "annotations/1"
    media_duration: float | None = None
    "The duration of the media, if known"
    annotations: list[Annotation] = Field(default_factory=list)
    "The annotations for this media"

    def merge_instances(self):
        """Sometimes tools will return multiple annotations for the same thing
           that only differs in their instances.  Merge them together"""
        if not self.annotations:
            return

        # this is an inefficient implementation O(2n)?, but it's easy to write        
        res: list[Annotation] = []
        while len(self.annotations):
            this = self.annotations.pop(0)
            for r in res:
                if r.can_merge_instances(this):
                    r.instances.extend(this.instances)
                    break
            else:
                res.append(this)

        self.annotations = res



