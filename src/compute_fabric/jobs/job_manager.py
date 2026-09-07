from dataclasses import dataclass

from compute_fabric.common.enums import JobStatus
from compute_fabric.execution.workload_spec import WorkloadSpec
from compute_fabric.storage.repository import JobRepository


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
    workload_id: str | None = None
    workload_spec: WorkloadSpec | None = None


class JobManager:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def submit_job(self, job: Job) -> None:
        self.repository.save(job)

    def update_job(self, job: Job) -> None:
        self.repository.save(job)

    def get_job(self, job_id: str) -> Job | None:
        return self.repository.get(job_id)

    def list_jobs(self) -> list[Job]:
        return self.repository.list_all()

    def remove_job(self, job_id: str) -> None:
        self.repository.delete(job_id)
