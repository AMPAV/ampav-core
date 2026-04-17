"""
General purpos utilities
"""
import yaml
from pydantic import BaseModel


def duration2hhmmss(duration: float) -> str:
    """
    Take a duration in seconds and convert it to hh:mm:ss.sss
    
    :param timestamp: Number of seconds to convert
    :return: Human-readable duration string
    :rtype: str
    """
    hours = int(duration / 3600)
    duration -= hours * 3600
    minutes = int(duration / 60)
    seconds = duration - minutes * 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def hhmmss2seconds(hhmmss: str) -> float:
    """
    Convert a duration string in the format of hh:mm:ss.sss to seconds
    
    :param hhmmss: Human readable duration string
    :return: Number of seconds represented by the string
    :rtype: float
    """
    parts = hhmmss.split(":")
    if len(parts) == 1:
        # looks like it was just seconds
        return float(hhmmss)
    elif len(parts) == 2:
        # mm:ss
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        # hh:mm:ss
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"Can't recognize format of {hhmmss}")
 

def pretty_yaml(thing: object, **kwargs) -> str:
    if isinstance(thing, BaseModel):
        thing = thing.model_dump(exclude_none=True)
    return yaml.safe_dump(thing, **kwargs)


