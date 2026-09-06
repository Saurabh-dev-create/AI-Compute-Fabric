from typing import TYPE_CHECKING

from compute_fabric.storage.repository import JobRepository

if TYPE_CHECKING:
    from compute_fabric.jobs.job_manager import Job


class InMemoryJobRepository(JobRepository):
    def __init__(self) -> None:
        self._jobs: dict[str, "Job"] = {}

    def save(self, job: "Job") -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> "Job | None":
        return self._jobs.get(job_id)

    def list_all(self) -> list["Job"]:
        return list(self._jobs.values())

    def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
