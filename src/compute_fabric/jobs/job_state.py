from compute_fabric.common.enums import JobStatus
from compute_fabric.jobs.job_manager import Job


class JobStateManager:
    def set_status(self, job: Job, status: JobStatus) -> None:
        job.status = status

    def schedule(self, job: Job) -> None:
        self.set_status(job, JobStatus.SCHEDULED)

    def start(self, job: Job) -> None:
        self.set_status(job, JobStatus.RUNNING)

    def complete(self, job: Job) -> None:
        self.set_status(job, JobStatus.COMPLETED)

    def fail(self, job: Job) -> None:
        self.set_status(job, JobStatus.FAILED)

    def cancel(self, job: Job) -> None:
        self.set_status(job, JobStatus.CANCELLED)
