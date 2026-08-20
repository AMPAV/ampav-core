import logging
from pathlib import Path
import time

from ampav.core.logging import LOG_FORMAT
from ampav.core.utils import dump_data
from ..schema.tool import ToolOutput
from ..schema.transcript import Transcript
from ..schema.segments import WordSegment
import argparse
from .webvtt import paragraphs_to_webvtt
from ..schema.transcript import words_to_paragraphs
from ampav.core import __version__

def import_text_transcript(text: str) -> ToolOutput:
    """Take text and convert it to a transcript tool output"""
    xscript = ToolOutput(tool_name="text import",
                         tool_version=__version__,
                         start_time=time.time(),
                         output=Transcript())
    xscript.setup_logging()

    for word in text.split():
        xscript.output.words.append(WordSegment.from_str(word))

    xscript.output.text = " ".join([x.to_str() for x in xscript.output.words])
    
    xscript.output.paragraphs = words_to_paragraphs(xscript.output.words)
    xscript.end_time = time.time()
    return xscript


def cli_import_text_transcript():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument('file', help="text transcript file")
    parser.add_argument('output', type=Path, help="output file")
    parser.add_argument("--debug", action="store_true", help="enable debug logging")   
    parser.add_argument("--format", choices=['yaml', 'json', 'pickle'], default='yaml', help="Output format, default yaml")
    args = parser.parse_args()
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG if args.debug else logging.INFO)
    text = Path(args.file).read_text()
    xscript = import_text_transcript(text)
    xscript.parameters['filename'] = str(args.file)
    dump_data(xscript, args.format, args.output)
