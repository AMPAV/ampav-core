"""
General purpos utilities
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
import pickle
from functools import reduce
import json
import sys
from ampav.core.schema.basemodel import AmpAVBaseModel
import re

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
            if isinstance(data, BaseModel):
                res = pickle.dumps(data.model_dump())
            else:
                res = pickle.dumps(data)
        case _:
            raise ValueError(f"Unknown data format {format}")
    if output is None:
        if isinstance(res, bytes):
            sys.stdout.buffer.write(res)
        else:
            print(res)
    else:
        if isinstance(res, bytes):
            output.write_bytes(res)
        else:
            output.write_text(res)


def load_data(file: Path, allow_pickle: bool=False) -> dict:
    """Load dict data from a file in pickle, json, or yaml format"""
    data = file.read_bytes()
    if allow_pickle:
        try:
            return pickle.loads(data)
        except pickle.PickleError:
            pass
    try:
        data = str(data, encoding='utf-8')
    except UnicodeDecodeError:
        raise Exception("Cannot load binary file.  If it's in pickle format, allow_pickle")

    return yaml.safe_load(data)
    

def key_finder(data: Any, key: str) -> list:
    """Find the values for the given key no matter where
       it is in the data structure"""
    res = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                res.append(v)
            else:
                if isinstance(v, dict):
                    res.extend(key_finder(v, key))
                elif isinstance(v, (list, set, tuple)):
                    for i in v:
                        res.extend(key_finder(i, key))
    elif isinstance(data, (set, list, tuple)):
        for i in data:
            res.extend(key_finder(i, key))

    return res


def pt2seconds(pt: str) -> float:
    """Azure (and maybe others) sometimes returns times in PTxHxMxS format,
       this will parse it and return it as seconds"""
    if m := re.match(r'PT((?P<hours>\d+)H)?((?P<minutes>\d+)M)?((?P<seconds>\d+(\.\d+)?)S)?$', pt):
        parts = {k: float(v) if v else 0 for k, v in m.groupdict().items()}
        return (3600 * parts.get('hours', 0)) + (60 * parts.get('minutes', 0)) + parts.get('seconds', 0)
    else:
        raise ValueError(f"This doesn't appear to be a Point Time: {pt}, {m}")
    

def seconds2pt(duration: float) -> float:
    """Convert seconds to a point in time:  PTxHxMxS"""
    hours = int(duration / 3600)
    duration -= hours * 3600
    minutes = int(duration / 60)
    seconds = duration - minutes * 60
    if hours:
        return f"PT{hours}H{minutes}M{seconds:0.2f}S"
    if minutes:
        return f"PT{minutes}M{seconds:0.2f}S"    
    return f"PT{seconds:0.2f}S"
    