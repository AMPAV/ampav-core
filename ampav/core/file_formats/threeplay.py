from ..schema.tool import ToolOutput
from ..schema.transcript import Transcript, words_to_paragraphs
from ..schema.segments import ParagraphSegment, WordSegment
import argparse
import json
from .webvtt import paragraphs_to_webvtt
from copy import deepcopy

def import_threeplay_json(threeplay: dict) -> ToolOutput:
    """Take a threeplay data structure and convert it to
       a transcript tool output"""
    
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
    transcript = Transcript(text="\n".join([x.text for x in paragraphs]),                                                                         
                            paragraphs=paragraphs,
                            words=words)
    out = ToolOutput(tool_name="3Play",
                    output=transcript)
    return out


def cli_import_threeplay_json():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help="3Play JSON file")
    parser.add_argument("--webvtt", action="store_true", help="Dump webvtt instead of yaml")
    args = parser.parse_args()
    with open(args.file) as f:
        data = json.load(f)

    xscript = import_threeplay_json(data)
    #print(xscript.output.paragraphs)
    if args.webvtt:
        # we're going to restructure the paragraphs that came from 3play to
        # make them more VTT friendly.
        print(paragraphs_to_webvtt(words_to_paragraphs(xscript.output.words)))
    else:
        print(xscript.model_dump_yaml())


if __name__ == "__main__":
    cli_import_threeplay_json()