"""Common base API for AMPAV tools backed by remote asynchronous jobs."""

import time
from enum import StrEnum, auto
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from ampav.core.schema.tool import ToolOutput

InputT = TypeVar("InputT")
JobRefT = TypeVar("JobRefT")
ExternalResultT = TypeVar("ExternalResultT")


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

    The default policy deletes nothing. Implementations should never delete
    caller-owned/pre-existing input data unless explicitly requested.
    """

    delete_job: bool = False
    delete_input: bool = False
    delete_output: bool = False


class AsyncTool(Generic[InputT, JobRefT, ExternalResultT]):
    """Base class for AMPAV tools that run as remote asynchronous jobs."""

    polling_interval: float = 30
    timeout: float | None = None
    cleanup_policy: CleanupPolicy = CleanupPolicy()

    def submit(self, provider_input: InputT, *args: Any, **kwargs: Any) -> JobRefT:
        """Submit provider-native input and return a provider-native job reference.

        For cloud tools, `provider_input` is commonly an external URI or a
        provider-specific request object.
        """
        raise NotImplementedError

    def get_status(self, job: JobRefT) -> AsyncJobStatus:
        """Return lightweight progress/status information for a job."""
        raise NotImplementedError

    def get_job(self, job: JobRefT) -> Any:
        """Return provider-specific full job details."""
        raise NotImplementedError

    def is_done(self, job: JobRefT) -> bool:
        """Return true when the job has reached a terminal state."""
        return self.get_status(job).is_done

    def get_external_result(self, job: JobRefT) -> ExternalResultT | None:
        """Return the provider-native result if it is ready, otherwise return None."""
        raise NotImplementedError

    def to_tool_output(self, job: JobRefT, result: ExternalResultT) -> ToolOutput:
        """Convert a provider-native result into an AMPAV ToolOutput."""
        raise NotImplementedError

    def cleanup(self, job: JobRefT, cleanup_policy: CleanupPolicy | None = None) -> None:
        """Clean up resources selected by the cleanup policy.
        Implementations may not be able to delete in-progress provider jobs.
        """
        raise NotImplementedError

    def list_jobs(self) -> Any:
        """Return provider-native job listing data."""
        raise NotImplementedError

    def process(
        self,
        provider_input: InputT,
        *args: Any,
        **kwargs: Any,
    ) -> ToolOutput:
        """Submit provider-native input, wait for completion, clean up, and return AMPAV output.

        For AMPAV pipeline input, use `process_ampav_input()` so subclasses can
        extract and adapt the relevant `ToolOutput.output` data first.
        """
        job = self.submit(provider_input, *args, **kwargs)
        started = time.monotonic()
        status = self.get_status(job)

        while not status.is_done:
            if self.timeout is not None and time.monotonic() - started > self.timeout:
                self.cleanup(job, self.cleanup_policy)
                raise ToolError(f"Async job {status.job_id!r} did not finish within {self.timeout} seconds")
            time.sleep(self.polling_interval)
            status = self.get_status(job)

        if status.status != AsyncStatusCode.SUCCEEDED:
            self.cleanup(job, self.cleanup_policy)
            message = status.message or "no provider message"
            raise ToolError(f"Async job {status.job_id!r} ended with status {status.status}: {message}")

        external_result = self.get_external_result(job)
        if external_result is None:
            self.cleanup(job, self.cleanup_policy)
            raise ToolError(f"Async job {status.job_id!r} succeeded without an available result")

        output = self.to_tool_output(job, external_result)
        self.cleanup(job, self.cleanup_policy)
        return output

    def process_ampav_input(
        self,
        ampav_input: ToolOutput,
        *args: Any,
        **kwargs: Any,
    ) -> ToolOutput:
        """Adapt upstream AMPAV ToolOutput data and process it through this tool."""
        raise NotImplementedError
