"""Common base API for AMPAV tools backed by remote asynchronous jobs."""

import time
from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel, Field

from ampav.core.schema.tool import ToolOutput


class AsyncStatusCode(StrEnum):
    """Common async job states across remote tool providers."""

    QUEUED = auto()
    IN_PROGRESS = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    CANCELED = auto()
    PARTIAL_SUCCESS = auto()


class ToolError(RuntimeError):
    """Base exception for tool-level execution failures."""


class AsyncJobStatus(BaseModel):
    """Serializable base status for a remote async job.

    Providers may return subclasses with additional provider-specific fields.
    `progress` is a percentage in the range 0-100. Providers that do not expose
    progress should leave it at 0 until the job reaches a terminal status.
    """

    job_id: str
    status: AsyncStatusCode
    progress: float = Field(default=0, ge=0, le=100)
    message: str | None = None

    @property
    def is_done(self) -> bool:
        """Return true when the remote job no longer needs polling."""
        return self.status in {
            AsyncStatusCode.SUCCEEDED,
            AsyncStatusCode.FAILED,
            AsyncStatusCode.CANCELED,
            AsyncStatusCode.PARTIAL_SUCCESS,
        }


class AsyncTool:
    """Base class for AMPAV tools that run as remote asynchronous jobs."""

    polling_interval: float = 30
    timeout: float | None = None
    cleanup: bool = True

    def submit(self, *args: Any, **kwargs: Any) -> Any:
        """Submit a remote async job and return the provider job handle.

        Providers may return any handle type they can pass back to the other
        lifecycle methods. Prefer serializable handles when practical.
        """
        raise NotImplementedError

    def get_status(self, job: Any, *, details: bool = False) -> AsyncJobStatus:
        """Return progress/status information for a job.

        Keep the default call lightweight. Providers may include heavier
        provider-specific details when ``details`` is true.
        """
        raise NotImplementedError

    def is_done(self, job: Any) -> bool:
        """Return true when the job has reached a terminal state.

        Providers may override this when they have a cheaper completion check.
        """
        return self.get_status(job, details=False).is_done

    def cancel(self, job: Any) -> None:
        """Cancel a remote async job and clean up provider resources if possible."""
        raise NotImplementedError

    def get_result(self, job: Any) -> ToolOutput | None:
        """Return AMPAV output when ready, otherwise return None.

        Implementations provide provider-native retrieval and conversion through
        the internal hooks. Terminal failed/canceled/partial-success jobs raise
        ``ToolError`` and clean up resources created by the tool when cleanup is
        enabled.
        """
        status = self.get_status(job, details=False)
        if not status.is_done:
            return None

        try:
            if status.status != AsyncStatusCode.SUCCEEDED:
                message = status.message or "no provider message"
                raise ToolError(f"Async job {status.job_id!r} ended with status {status.status}: {message}")

            external_result = self._get_external_result(job)
            if external_result is None:
                raise ToolError(f"Async job {status.job_id!r} succeeded without an available result")

            return self._to_tool_output(job, external_result)
        finally:
            if self.cleanup:
                self._cleanup(job)

    def process(self, *args: Any, **kwargs: Any) -> ToolOutput:
        """Submit a job, wait for completion, clean up, and return AMPAV output."""
        job = self.submit(*args, **kwargs)
        started = time.monotonic()

        while not self.is_done(job):
            if self.timeout is not None and time.monotonic() - started > self.timeout:
                status = self.get_status(job, details=False)
                if self.cleanup:
                    self._cleanup(job)
                raise TimeoutError(f"Async job {status.job_id!r} did not finish within {self.timeout} seconds")
            time.sleep(self.polling_interval)

        result = self.get_result(job)
        if result is None:
            # get_result() owns terminal cleanup. Reaching this branch means
            # is_done() and get_result() disagreed, so avoid double cleanup.
            status = self.get_status(job, details=False)
            raise ToolError(f"Async job {status.job_id!r} finished without an available result")
        return result

    def _get_external_result(self, job: Any) -> Any | None:
        """Return the provider-native result if it is ready, otherwise return None."""
        raise NotImplementedError

    def _to_tool_output(self, job: Any, result: Any) -> ToolOutput:
        """Convert a provider-native result into an AMPAV ToolOutput."""
        raise NotImplementedError

    def _cleanup(self, job: Any) -> None:
        """Clean up temporary resources created by this tool."""
        return None
