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
        return self.status in {AsyncStatusCode.SUCCEEDED, AsyncStatusCode.FAILED, AsyncStatusCode.CANCELED}


class CleanupPolicy(BaseModel):
    """Common cleanup choices for async remote jobs.

    The default policy deletes nothing. Implementations should never delete
    caller-owned/pre-existing input data unless explicitly requested.
    """

    delete_job: bool = False
    delete_input: bool = False
    delete_output: bool = False


class AsyncTool:
    """Base class for AMPAV tools that run as remote asynchronous jobs."""

    polling_interval: float = 30
    timeout: float | None = None
    cleanup_policy: CleanupPolicy = CleanupPolicy()

    def submit(self, *args: Any, **kwargs: Any) -> str:
        """Submit a new job and return the provider job ID."""
        raise NotImplementedError

    def get_status(self, job_id: str) -> AsyncJobStatus:
        """Return lightweight progress/status information for a job."""
        raise NotImplementedError

    def get_job(self, job_id: str) -> Any:
        """Return provider-specific full job details."""
        raise NotImplementedError

    def is_done(self, job_id: str) -> bool:
        """Return true when the job has reached a terminal state."""
        return self.get_status(job_id).is_done

    def get_result(self, job_id: str) -> ToolOutput | None:
        """Return the result if it is ready, otherwise return None."""
        raise NotImplementedError

    def cleanup(self, job_id: str, cleanup_policy: CleanupPolicy | None = None) -> None:
        """Clean up resources selected by the cleanup policy.
        Implementations may not be able to delete in-progress provider jobs.
        """
        raise NotImplementedError

    def list_jobs(self) -> list[str]:
        """Return job IDs visible to this tool/provider."""
        raise NotImplementedError

    def run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> ToolOutput:
        """Submit a job, wait for completion, optionally clean up, and return its result."""
        job_id = self.submit(*args, **kwargs)
        started = time.monotonic()
        status = self.get_status(job_id)

        while not status.is_done:
            if self.timeout is not None and time.monotonic() - started > self.timeout:
                self.cleanup(job_id, self.cleanup_policy)
                raise TimeoutError(f"Async job {job_id!r} did not finish within {self.timeout} seconds")
            time.sleep(self.polling_interval)
            status = self.get_status(job_id)

        if status.status != AsyncStatusCode.SUCCEEDED:
            self.cleanup(job_id, self.cleanup_policy)
            message = status.message or "no provider message"
            raise RuntimeError(f"Async job {job_id!r} ended with status {status.status}: {message}")

        result = self.get_result(job_id)
        self.cleanup(job_id, self.cleanup_policy)
        if result is None:
            raise RuntimeError(f"Async job {job_id!r} succeeded without an available result")
        return result
