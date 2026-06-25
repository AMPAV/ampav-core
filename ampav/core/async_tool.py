"""Common base API for AMPAV tools backed by remote asynchronous jobs."""

import time
from enum import StrEnum, auto
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from ampav.core.schema.tool import ToolOutput
from ampav.core.schema.basemodel import AmpAVBaseModel


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


class AsyncJobStatus(AmpAVBaseModel):
    """Status of an async job.
    
    Implementors may return a subclass with additional information which would
    be populated when get_status(..., details=True).
    """
    model_config = ConfigDict(use_enum_values=True) # make sure the status is rendered

    job_id: str
    """An opaque job_id that is used to refer to the job"""

    status: AsyncStatusCode
    """The current job status"""

    progress: float = Field(default=0, ge=0, le=100)
    """Percentage of completion.  Only valid when the status is IN_PROGRESS"""

    message: str | None = None
    """Status message at this point in the processing"""

    @property
    def is_done(self) -> bool:
        """Return true if the async job is finished."""
        return self.status in {
            AsyncStatusCode.SUCCEEDED,
            AsyncStatusCode.FAILED,
        }


class AsyncTool:
    """Base class for asynchronous AMPAV tools."""

    polling_interval: float = 30
    """Default Polling interval to check if finished.  May be ignored by
       implementations that uses other methods to check if a job has completed"""

    def submit(self, *args: Any, **kwargs: Any) -> str:
        """Submit an async job and return a job id string."""
        raise NotImplementedError("submit must be implemented by the tool")


    def list_jobs(self) -> list[AsyncJobStatus]:
        """Return a list of job status info for all jobs known by the implementation
        
        Note: The implementation should restrict the returned jobs to ones that the
        library tool has created, but this is not guaranteed.
        """
        raise NotImplementedError("list_jobs must be implemented by the tool")


    def get_status(self, job_id: str, details: bool = True) -> AsyncJobStatus:
        """Return progress/status information for a job.

        Implementors may include additional provider-specific details when 
        `details` is true.

        If the job doesn't exist, a KeyError will be raised

        Note:  The default value of `details` may vary from tool to tool.
        """
        raise NotImplementedError("get_status must be implemented by the tool")


    def is_done(self, job_id: str) -> bool:
        """Return true when the job has reached a terminal state.
        
        If the job doesn't exist, a KeyError will be raised
        """
        return self.get_status(job_id, details=False).is_done


    def get_result(self, job_id: str) -> ToolOutput | None:
        """Return AMPAV tool output when ready, otherwise return None.

        When the result has been successfully retrieved the job will be
        cleaned up.

        If the job doesn't exist, a KeyError will be raised.

        Failed jobs will be cleaned up and raise a ToolError with relevant details.
        """
        raise NotImplementedError("get_result must be implemented by the tool")


    def process(self, *args: Any, **kwargs: Any) -> ToolOutput:
        """Run the tool and wait for the output.
        
        Generally the implementation will:
        * Submit a job
        * wait for completion
        * clean up
        * return AMPAV tool output.
        
        """
        job_id = self.submit(*args, **kwargs)
        while not self.is_done(job_id):
            time.sleep(self.polling_interval)

        result = self.get_result(job_id)
        if result is None:
            # get_result() owns terminal cleanup. Reaching this branch means
            # is_done() and get_result() disagreed, so avoid double cleanup.
            raise ToolError(f"Async job {job_id} finished without an available result")
        return result


    @staticmethod
    def native_to_tool_output(native: Any) -> ToolOutput:
        """Convert a native result data structure (such as raw AWS Transcribe
        data) into an AMPAV ToolOutput."""
        raise NotImplementedError("native_to_tool_output must be implemented by the tool")


    def cleanup(self, job_id: str) -> None:
        """Clean up temporary resources created by this job.
        
        * If the job_id doesn't exist, do nothing
        * If the job is queued, dequeue it and clean up
        * If the job is running, stop the job and clean up
        * If the job has finished, clean up resources.

        This call is blocking and will wait until finished.  If a native job
        appears to be hung this method may raise an exception.
        """
        raise NotImplementedError("cleanup must be implemented by the tool")

    