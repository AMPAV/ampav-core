"""Common base API for AMPAV tools backed by remote asynchronous jobs."""

import time
from enum import StrEnum, auto
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from ampav.core.schema.tool import ToolOutput


class AsyncStatusCode(StrEnum):
    """Common async job states across remote tool providers."""
    QUEUED = auto()
    IN_PROGRESS = auto()
    SUCCEEDED = auto()
    FAILED = auto()


class ToolError(RuntimeError):
    """Base exception for tool-level execution failures."""


class AsyncJobStatus(BaseModel):
    """Serializable base status for a remote async job.
    
    Providers may return subclasses with additional provider-specific fields.
    `progress` is a percentage in the range 0-100. Providers that do not expose
    progress should leave it at 0 until the job reaches a terminal status.
    """
    model_config = ConfigDict(use_enum_values=True) # make sure the status is rendered

    job_handle: str
    status: AsyncStatusCode
    progress: float = Field(default=0, ge=0, le=100)
    message: str | None = None

    @property
    def is_done(self) -> bool:
        """Return true when the remote job no longer needs polling."""
        return self.status in {
            AsyncStatusCode.SUCCEEDED,
            AsyncStatusCode.FAILED,
        }


class AsyncTool:
    """Base class for AMPAV tools that run as remote asynchronous jobs."""

    polling_interval: float = 30
    timeout: float | None = None

    def submit(self, *args: Any, **kwargs: Any) -> str:
        """Submit a async job and return a job handle.

        Providers may return any handle type they can pass back to the other
        lifecycle methods. Prefer serializable handles when practical.
        """
        raise NotImplementedError


    def cancel(self, job_handle: str) -> None:
        """Cancel an async job and clean up resources if possible."""
        raise NotImplementedError


    def list_jobs(self) -> list[Any]:
        """Return a list of job handles known by the provider"""
        raise NotImplementedError


    def get_status(self, job_handle: str, details: bool = True) -> AsyncJobStatus:
        """Return progress/status information for a job.

        Keep the default call lightweight. Providers may include heavier
        provider-specific details when ``details`` is true.
        """
        raise NotImplementedError


    def is_done(self, job_handle: str) -> bool:
        """Return true when the job has reached a terminal state.

        Providers may override this when they have a cheaper completion check.
        """
        return self.get_status(job_handle, details=False).is_done


    def get_result(self, job_handle: str) -> ToolOutput | None:
        """Return AMPAV output when ready, otherwise return None.

        Implementations provide provider-native retrieval and conversion through
        the internal hooks. Terminal failed/canceled jobs raise ``ToolError`` 
        """

        status = self.get_status(job_handle, details=False)
        if not status.is_done:
            return None

        try:
            if status.status != AsyncStatusCode.SUCCEEDED:
                message = status.message or "no provider message"
                raise ToolError(f"Async job {status.job_handle!r} ended with status {status.status}: {message}")

            native_result = self._get_native_result_hook(job_handle)
            if native_result is None:
                raise ToolError(f"Async job {status.job_handle!r} succeeded without an available result")
            tool_output = AsyncTool.native_to_tool_output(native_result)
            # Add any additional context to the tool
            self._finalize_tool_output_hook(job_handle, tool_output)
            return tool_output
        finally:
            self.cleanup(job_handle)


    def process(self, *args: Any, **kwargs: Any) -> ToolOutput:
        """Submit a job, wait for completion, clean up, and return AMPAV output."""
        job_handle = self.submit(*args, **kwargs)
        started = time.monotonic()

        while not self.is_done(job_handle):
            if self.timeout is not None and time.monotonic() - started > self.timeout:
                self.cleanup(job_handle)
                raise TimeoutError(f"Async job {job_handle!r} did not finish within {self.timeout} seconds")
            time.sleep(self.polling_interval)

        result = self.get_result(job_handle)
        if result is None:
            # get_result() owns terminal cleanup. Reaching this branch means
            # is_done() and get_result() disagreed, so avoid double cleanup.
            raise ToolError(f"Async job {job_handle!r} finished without an available result")
        return result


    def _get_native_result_hook(self, job_handle: str) -> Any | None:
        """Provider hook: Return the provider-native result if it is ready, otherwise return None."""
        raise NotImplementedError


    def _finalize_tool_output_hook(self, job_handle: str, tool_output: ToolOutput) -> None:
        """Provider hook: Update fields in the given tool_output to provide 
           more context, such as timing information, logs, input/output files, 
           etc."""
        pass

    @staticmethod
    def native_to_tool_output(native: Any) -> ToolOutput:
        """Convert a provider-native result into an AMPAV ToolOutput."""
        raise NotImplementedError


    def cleanup(self, job_handle: Any) -> None:
        """Clean up temporary resources created by this tool."""
        return NotImplementedError
