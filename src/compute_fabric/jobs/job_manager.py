from dataclasses import dataclass

from compute_fabric.common.enums import JobStatus


@dataclass
class Job:
    id: str
    job_type: str
    gpu_type: str | None
    min_vram_gb: float
    priority: int
    status: JobStatus = JobStatus.PENDING
    gpu_id: str | None = None
    node_id: str | None = None
    allocated_vram_gb: float | None = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def submit_job(self, job: Job) -> None:
        self._jobs[job.id] = job

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[Job]:
        return list(self._jobs.values())

    def remove_job(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
