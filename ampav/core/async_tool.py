from dataclasses import dataclass
from enum import StrEnum, auto
import time
from typing import Any

from ampav.core.schema.tool import ToolOutput

# Implementor's notes:
# * If someone refers to a job_id that doesn't exist, throw a KeyError
# * The constructor, submit, and run methods should allow arbitrary keyword
#   parameters to propagate to the underlying implementation's methods.  For
#   example, boto3 allows all kinds of environment tweaks and we don't want to
#   re-implement all of those choices.


class AsyncStatusCode(StrEnum):
    IN_PROGRESS = auto()
    FINISHED = auto()
    ERROR = auto()


@dataclass
class AsyncJobStatus:
    job_id: Any
    status: AsyncStatusCode
    progress: float


class AsyncTool:
    def __init__(self, *args, **kwargs):
        self.polling_interval = 30  # completion retry interval
        ...


    def submit(self, *args, **kwargs) -> Any:
        """Submit a new job, returning the job's id"""
        ...


    def get_status(self, job_id: Any) -> AsyncJobStatus:            
        "Return the status of a job"
        ...


    def is_done(self, job_id: Any) -> bool:
        """Return True if the job is done"""
        return self.get_status(job_id)[1] >= 100
            

    def get_result(self, job_id: Any) -> ToolOutput | None:
        """Get the result if it is ready, otherwise return None"""
        ...


    def cleanup(self, job_id: Any):
        """Clean up a job, killing it if it is still in progress.
           Also remove any resources automatically allocated"""
        ...


    def list_jobs(self) -> list[Any]:
        """Get the job ids that are in the system"""
        ...


    def run(self, *args, **kwargs) -> ToolOutput:
        """Submit a job, wait for it to complete, and clean up when finished."""
        job = self.submit(*args, **kwargs)
        while not self.is_done(job):
            time.sleep(self.polling_interval)
        res = self.get_result(job)
        self.cleanup(job)
        return res
    
        
