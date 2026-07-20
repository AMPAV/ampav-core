"""
General purpos utilities
"""

from pathlib import Path

import yaml
from pydantic import BaseModel
import pickle
from functools import reduce
import json

from ampav.core.schema.basemodel import AmpAVBaseModel

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


def rsetattr(obj, attr: str, val):
    """Set an object attribute handling dotted notation"""
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    """Get an object attribute handling dotted notation"""
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))


def dump_data(data: AmpAVBaseModel | dict, format: Path, output: Path=None, **kwargs):
    """Dump a dict, pydantic BaseModel or AmpAVBaseModel to a Path, or stdout
       if output is None"""
    match format:
        case "yaml":
            if isinstance(data, AmpAVBaseModel):
                res = data.model_dump_yaml(**kwargs)
            elif isinstance(data, BaseModel):
                res = yaml.safe_dump(data.model_dump())
            else:
                res = yaml.safe_dump(data, **kwargs)            
        case "json":
            if isinstance(data, BaseModel):
                res = data.model_dump_json(**kwargs)
            else:
                res = json.dumps(data, **kwargs)
        case "pickle":
            res = pickle.dumps(data)
        case _:
            raise ValueError(f"Unknown data format {format}")
    if output is None:
        print(res)
    else:
        if format == "pickle":
            output.write_bytes(res)
        else:
            output.write_text(res)


def load_data(file: Path) -> dict:
    """Load dict data from a file in pickle, json, or yaml format"""
    data = file.read_bytes()
    try:
        return pickle.loads(data)
    except pickle.PickleError:
        return yaml.safe_load(str(data, encoding='utf-8'))
    