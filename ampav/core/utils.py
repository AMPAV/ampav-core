"""
General purpos utilities
"""
from enum import StrEnum, auto
from typing import Any

import yaml
from pydantic import BaseModel
from functools import reduce

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


class AsyncTool:
    def __init__(self, *args, **kwargs):
        ...


    def submit(self, *args, **kwargs) -> Any:
        """Submit a new job, returning the job's id"""
        ...


    # If someone refers to a job_id that doesn't exist, throw a KeyError

    class StatusCode(StrEnum):
        IN_PROGRESS = auto()
        FINISHED = auto()
        ERROR = auto()


    class JobStatus():
        job_id: Any
        status: "AsyncTool.StatusCode"
        progress: float


    def get_status(self, job_id: Any) -> "AsyncTool.JobStatus":
        "Return the status of a job"
        ...


    def is_done(self, job_id: Any) -> bool:
        """Return True if the job is done"""
        return self.get_status(job_id)[1] >= 100
            

    def get_result(self, job_id: Any, wait: bool=True, polling_interval: float=30) -> Any | None:
        """If wait is True (the default), wait until the job has finished and return the results
           If wait is not True, return the results if they are ready otherwise None
           Polling_interval is used when waiting for results"""
        ...


    def delete(self, job_id: Any):
        """Delete a job, killing it if it is still in progress.
           Also remove any resources allocated"""
        ...


    def list_jobs(self) -> list[Any]:
        """Get the jobs that are in the system"""
        ...

