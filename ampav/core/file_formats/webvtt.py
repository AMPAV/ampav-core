import argparse
import logging
from pathlib import Path

from ampav.core.logging import LOG_FORMAT

from ..schema.segments import ParagraphSegment
from ..utils import duration2hhmmss
from .. import __version__
from ampav.core.schema import load_ampav_file

def paragraphs_to_webvtt(paras: list[ParagraphSegment]) -> str:
    res = "WEBVTT\n\n"
    for p in paras:
        start = duration2hhmmss(p.start_time if p.start_time else 0)
        end = duration2hhmmss(p.end_time if p.end_time else 0)
        res += f"{start} --> {end}\n"        
        if p.speaker is not None:
            res += f"<v {p.speaker}>"
        res += p.text + "\n\n"
    return res


def cli_transcript_to_webvtt():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logging")   
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--allow_pickle", action="store_true", help="Allow loading of pickle files")
    parser.add_argument('file', type=Path, help="text transcript file")
    parser.add_argument('output', type=Path, help="output vtt file")
    args = parser.parse_args()
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG if args.debug else logging.INFO)                        
    transcript = load_ampav_file(args.file, args.allow_pickle)

    args.output.write_text(paragraphs_to_webvtt(transcript.output.paragraphs))

    