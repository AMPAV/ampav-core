from ...schema.segments import ParagraphSegment
from ...utils import duration2hhmmss

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