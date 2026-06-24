"""Common base API for AMPAV tools backed by remote asynchronous jobs."""

import time
from enum import StrEnum, auto
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from ampav.core.schema.tool import ToolOutput


class AsyncStatusCode(StrEnum):
    """Common async job status codes."""
    QUEUED = auto()
    """The job is queued and hasn't started processing"""
    
    IN_PROGRESS = auto()
    """The job is currently processing"""

    SUCCEEDED = auto()
    """The job has successfully completed"""

    FAILED = auto()
    """The job has failed"""


class ToolError(RuntimeError):
    """Base exception for tool-level execution failures."""


class AsyncJobStatus(BaseModel):
    """Status of an async job.
    
    Implementors may return a subclass with additional information which would
    be populated when get_status(..., details=True).
    """
    model_config = ConfigDict(use_enum_values=True) # make sure the status is rendered

    job_handle: str
    """An opaque handle that is used to refer to the job"""

    status: AsyncStatusCode
    """The current job status"""

    progress: float = Field(default=0, ge=0, le=100)
    """Percentage of completion.  Only valid when the status is IN_PROGRESS"""

    message: str | None = None
    """Status message at this point in the processing"""

    @property
    def is_done(self) -> bool:
        """Return true if the remote job is finished."""
        return self.status in {
            AsyncStatusCode.SUCCEEDED,
            AsyncStatusCode.FAILED,
        }


class AsyncTool:
    """Base class for asynchronous AMPAV tools."""

    polling_interval: float = 30

    def submit(self, *args: Any, **kwargs: Any) -> str:
        """Submit a async job and return a job handle string."""
        raise NotImplementedError("submit must be implemented by the tool")


    def list_jobs(self) -> list[str]:
        """Return a list of job handles known by the implementation"""
        raise NotImplementedError("list_jobs must be implemented by the tool")


    def get_status(self, job_handle: str, details: bool = True) -> AsyncJobStatus:
        """Return progress/status information for a job.

        Implementors may include additional provider-specific details when 
        `details` is true.

        If the job doesn't exist, a KeyError will be raised
        """
        raise NotImplementedError("get_status must be implemented by the tool")


    def is_done(self, job_handle: str) -> bool:
        """Return true when the job has reached a terminal state.
        
        If the job doesn't exist, a KeyError will be raised
        """
        return self.get_status(job_handle, details=False).is_done


    def get_result(self, job_handle: str) -> ToolOutput | None:
        """Return AMPAV tool output when ready, otherwise return None.

        When the result is has been successfully retrieved the job will be
        cleaned up.

        If the job doesn't exist, a KeyError will be raised.

        Failed jobs will raise a ToolError with relevant details.
        """
        raise NotImplementedError("get_result must be implemented by the tool")


    def process(self, *args: Any, **kwargs: Any) -> ToolOutput:
        """Submit a job, wait for completion, clean up, and return AMPAV tool output."""
        job_handle = self.submit(*args, **kwargs)
        while not self.is_done(job_handle):
            time.sleep(self.polling_interval)

        result = self.get_result(job_handle)
        if result is None:
            # get_result() owns terminal cleanup. Reaching this branch means
            # is_done() and get_result() disagreed, so avoid double cleanup.
            raise ToolError(f"Async job {job_handle!r} finished without an available result")
        return result


    @staticmethod
    def native_to_tool_output(native: Any) -> ToolOutput:
        """Convert a native result data structure (such as raw AWS Transcribe
        data) into an AMPAV ToolOutput."""
        raise NotImplementedError("native_to_tool_output must be implemented by the tool")


    def cleanup(self, job_handle: str) -> None:
        """Clean up temporary resources created by this job.
        
        * If the job_handle doesn't exist, do nothing
        * If the job is queued, dequeue it and clean up
        * If the job is running, stop the job and clean up
        * If the job has finished, clean up resources.

        """
        raise NotImplementedError("cleanup must be implemented by the tool")

    