from ...schema.tool import ToolOutput
from ...schema.transcript import Transcript
from ...schema.segments import ParagraphSegment, WordSegment
from itertools import pairwise
import argparse
import json
from ...formats.transcript.webvtt import paragraphs_to_webvtt

def import_threeplay_json(threeplay: dict) -> ToolOutput:
    """Take a threeplay data structure and convert it to
       a transcript tool output"""
    
    # read the paragraphs information to create the necessary time ranges
    paragraph_segs: list[ParagraphSegment] = {}
    word_segs = []
    for start, stop in pairwise(threeplay['paragraphs']):
        start /= 1000
        stop /= 1000
        paragraph_segs[(start, stop)] = ParagraphSegment(start_time=start,
                                                              end_time=stop,
                                                              speaker=None,
                                                              text='')
        
    def find_paridx(time):
        for k in paragraph_segs.keys():
            if k[0] <= time < k[1]:
                return k
        return None
    
    # assign the speakers to the paragraphs
    speaker_indexes = set()
    for idx, speaker in threeplay['speakers'].items():
        speaker_indexes.add(idx)
        idx = int(idx) / 1000
        paragraph_segs[find_paridx(idx)].speaker = speaker
            
    # remove the words which are the speaker word.
    threeplay['words'] = [x for x in threeplay['words'] if x[0] not in speaker_indexes]
        
    # generate the paragraph and timed words 
    for this, next in pairwise(threeplay['words']): 
        if this[1] != '':
            start = int(this[0]) / 1000
            end = int(next[0]) / 1000
            paridx = find_paridx(start)
            word_segs.append(WordSegment.from_str(this[1],
                                                    start_time=start,
                                                    end_time=end,
                                                    speaker=paragraph_segs[paridx].speaker))
            paragraph_segs[paridx].text += this[1] + " "
    
    # sort paragraphs, remove empty ones, and trim trailing whitespace
    paragraphs: list[ParagraphSegment] = sorted(paragraph_segs.values(), key=lambda x: x.start_time)    
    paragraphs = [x for x in paragraphs if x.text != '']
    for x in paragraphs:
        x.text = x.text.rstrip()

    transcript = Transcript(text="\n".join([x.text for x in paragraphs]),                                                                         
                            paragraphs=paragraphs,
                            words=word_segs)
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
    if args.webvtt:
        print(paragraphs_to_webvtt(xscript.output.paragraphs))
    else:
        print(xscript.model_dump_yaml())