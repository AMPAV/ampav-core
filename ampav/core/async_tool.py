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
    `progress` is a percentage in the range 0-100 when the provider exposes it.
    """

    job_id: str
    status: AsyncStatusCode
    progress: float | None = Field(default=None, ge=0, le=100)
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


class CleanupPolicy(BaseModel):
    """Common cleanup choices for async remote jobs.

    Passing ``None`` as the cleanup policy means the provider should apply its
    default cleanup behavior, usually deleting temporary resources created by
    the tool while leaving caller-provided inputs alone.
    """

    delete_job: bool = False
    delete_input: bool = False
    delete_output: bool = False


class AsyncTool:
    """Base class for AMPAV tools that run as remote asynchronous jobs."""

    polling_interval: float = 30
    timeout: float | None = None
    cleanup_policy: CleanupPolicy | None = None

    def submit(self, *args: Any, **kwargs: Any) -> Any:
        """Submit a remote async job and return the provider job handle."""
        raise NotImplementedError

    def get_status(self, job: Any) -> AsyncJobStatus:
        """Return lightweight progress/status information for a job."""
        raise NotImplementedError

    def is_done(self, job: Any) -> bool:
        """Return true when the job has reached a terminal state."""
        return self.get_status(job).is_done

    def get_result(self, job: Any) -> ToolOutput | None:
        """Return AMPAV output when ready, otherwise return None.

        Implementations provide provider-native retrieval and conversion through
        the internal hooks. Terminal failed/canceled jobs raise ``ToolError``.
        """
        status = self.get_status(job)
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
            self._cleanup(job, self.cleanup_policy)

    def process(self, *args: Any, **kwargs: Any) -> ToolOutput:
        """Submit a job, wait for completion, clean up, and return AMPAV output."""
        job = self.submit(*args, **kwargs)
        started = time.monotonic()

        while not self.is_done(job):
            if self.timeout is not None and time.monotonic() - started > self.timeout:
                self._cleanup(job, self.cleanup_policy)
                status = self.get_status(job)
                raise ToolError(f"Async job {status.job_id!r} did not finish within {self.timeout} seconds")
            time.sleep(self.polling_interval)

        result = self.get_result(job)
        if result is None:
            status = self.get_status(job)
            raise ToolError(f"Async job {status.job_id!r} finished without an available result")
        return result

    def _get_external_result(self, job: Any) -> Any | None:
        """Return the provider-native result if it is ready, otherwise return None."""
        raise NotImplementedError

    def _to_tool_output(self, job: Any, result: Any) -> ToolOutput:
        """Convert a provider-native result into an AMPAV ToolOutput."""
        raise NotImplementedError

    def _cleanup(self, job: Any, cleanup_policy: CleanupPolicy | None = None) -> None:
        """Clean up resources selected by the cleanup policy."""
        return None
