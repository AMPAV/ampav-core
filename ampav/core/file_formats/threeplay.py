import logging
from pathlib import Path
import time

from ampav.core.logging import LOG_FORMAT
from ampav.core.utils import dump_data

from ..schema.tool import ToolOutput
from ..schema.transcript import Transcript
from ..schema.segments import ParagraphSegment, WordSegment
import argparse
import json
from copy import deepcopy
from ampav.core import __version__

def import_threeplay_json(threeplay: dict) -> ToolOutput:
    """Take a threeplay data structure and convert it to
       a transcript tool output"""
    out = ToolOutput(tool_name="3Play",
                     start_time=time.time(),                     
                     tool_version=__version__)
    out.setup_logging()
    # making lots of changes in place, so don't destroy the thing we were passed
    threeplay = deepcopy(threeplay)
    # Get media length
    media_length = int(threeplay['words'][-1][0]) / 1000

    # Assign speakers to words ... stupidly inefficient, but I'm lazy.
    speaker = None
    threeplay['words'] = [[x[0], x[1], speaker, 0] for x in threeplay['words']]
    for idx, spk in threeplay['speakers'].items():
        if spk == '-':
            spk = None
        for w in threeplay['words']:
            if int(w[0]) >= int(idx):
                w[2] = spk

    # populate end time
    for i in range(len(threeplay['words']) - 1):
        threeplay['words'][i][3] = threeplay['words'][i + 1][0]
    threeplay['words'][-1][3] = threeplay['words'][-1][0]
    
    # remove the speaker words
    threeplay['words'] = [x for x in threeplay['words'] if x[0] not in list(threeplay['speakers'].keys())]

    # remove the empty words, convert the offsets to ints
    threeplay['words'] = [[int(x[0]), x[1], x[2], int(x[3])] for x in threeplay['words'] if x[1] != '']

    # split into paragraphs
    paras: list[list[WordSegment]] = []
    cur_para = []
    threeplay['paragraphs'].append(1_000_000)
    for i in range(len(threeplay['paragraphs']) - 1):
        step = threeplay['paragraphs'][i + 1]
        while threeplay['words'] and threeplay['words'][0][0] < step:
            word = threeplay['words'].pop(0)        
            cur_para.append(WordSegment.from_str(word[1], start_time=word[0]/1000,
                                                end_time=word[3]/1000, speaker=word[2]))
        if cur_para:
            paras.append(cur_para)
        cur_para = []
    
    # convert the paras...   
    paragraphs: list[ParagraphSegment] = [ParagraphSegment(start_time=x[0].start_time,
                                                           end_time=x[-1].end_time,
                                                           speaker=x[0].speaker,
                                                           text=' '.join([y.to_str() for y in x])) for x in paras if x]
    words = []
    for x in paras:
        words.extend(x)
    out.output = Transcript(text="\n".join([x.text for x in paragraphs]),                                                                         
                            paragraphs=paragraphs,
                            words=words)    
    out.end_time = time.time()
    return out


def cli_import_threeplay_json():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument('file', help="3Play JSON file")
    parser.add_argument('output', type=Path, help="output file")
    parser.add_argument("--format", choices=['yaml', 'json', 'pickle'], default='yaml', help="Output format, default yaml")
    args = parser.parse_args()
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG if args.debug else logging.INFO)
    with open(args.file) as f:
        data = json.load(f)

    xscript = import_threeplay_json(data)
    xscript.parameters['filename'] = str(args.file)
    dump_data(xscript, args.format, args.output)


if __name__ == "__main__":
    cli_import_threeplay_json()