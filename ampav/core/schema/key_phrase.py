from pydantic import Field
from typing import Literal

from .text_span import TextSpan, TextSpans


class KeyPhrase(TextSpan):
    """Key phrase mention found in source text."""

    pass


class KeyPhrases(TextSpans):
    """Key phrases extracted from source text."""

    ampav_format: Literal["key_phrases/1"] = "key_phrases/1"
    spans: list[KeyPhrase] = Field(default_factory=list, description="Key phrases found in the source text")
