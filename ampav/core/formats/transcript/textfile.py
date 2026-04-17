import logging
from pathlib import Path

from ampav.core.logging import LOG_FORMAT
from ...schema.tool import ToolOutput
from ...schema.transcript import Transcript
from ...schema.segments import ParagraphSegment, WordSegment
from itertools import pairwise
import argparse
import json
from ...formats.transcript.webvtt import paragraphs_to_webvtt
from ...formats.transcript.utils import words_to_paragraphs

def import_text_transcript(text: str) -> ToolOutput:
    """Take text and convert it to a transcript tool output"""
    xscript = ToolOutput(tool_name="text import",
                         tool_version="0.0.0",
                         output=Transcript())
    
    for word in text.split():
        xscript.output.words.append(WordSegment.from_str(word))

    xscript.output.paragraphs = words_to_paragraphs(xscript.output.words)
    return xscript


def cli_import_text_transcript():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help="text transcript file")
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument("--webvtt", action="store_true", help="Dump webvtt instead of yaml")    
    args = parser.parse_args()
    text = Path(args.file).read_text()
    xscript = import_text_transcript(text)

    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG if args.debug else logging.INFO)
    if args.webvtt:
        print(paragraphs_to_webvtt(xscript.output.paragraphs))
    else:
        print(xscript.model_dump_yaml())