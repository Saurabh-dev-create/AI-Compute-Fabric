from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.jobs.job_manager import Job, JobManager
from compute_fabric.jobs.job_state import JobStateManager
from compute_fabric.queue.queue_manager import QueueManager
from compute_fabric.queue.queue_processor import QueueProcessor
from compute_fabric.scheduler.scheduler import Scheduler, SchedulingDecision


class JobOrchestrator:
    def __init__(
        self,
        job_manager: JobManager,
        queue_manager: QueueManager,
        queue_processor: QueueProcessor,
        scheduler: Scheduler,
        state_manager: JobStateManager,
        gpu_manager: GPUManager,
    ) -> None:
        self.job_manager = job_manager
        self.queue_manager = queue_manager
        self.queue_processor = queue_processor
        self.scheduler = scheduler
        self.state_manager = state_manager
        self.gpu_manager = gpu_manager

    def submit_and_schedule(self, job: Job) -> SchedulingDecision | None:
        self.job_manager.submit_job(job)

        if not self.queue_manager.submit_job(job):
            return None

        return self.queue_processor.process_next()

    def start_job(self, job_id: str) -> bool:
        job = self.job_manager.get_job(job_id)

        if job is None:
            return False

        self.state_manager.start(job)

        return True

    def complete_job(self, job_id: str) -> bool:
        job = self.job_manager.get_job(job_id)

        if job is None:
            return False

        if job.gpu_id is not None:
            released = self.gpu_manager.release_gpu(
                job.gpu_id,
                job.allocated_vram_gb or job.min_vram_gb,
            )

            if not released:
                return False

        self.state_manager.complete(job)

        return True

    def fail_job(self, job_id: str) -> bool:
        job = self.job_manager.get_job(job_id)

        if job is None:
            return False

        if job.gpu_id is not None:
            released = self.gpu_manager.release_gpu(
                job.gpu_id,
                job.allocated_vram_gb or job.min_vram_gb,
            )

            if not released:
                return False

        self.state_manager.fail(job)

        return True

    def cancel_job(self, job_id: str) -> bool:
        job = self.job_manager.get_job(job_id)

        if job is None:
            return False

        if job.gpu_id is not None:
            released = self.gpu_manager.release_gpu(
                job.gpu_id,
                job.allocated_vram_gb or job.min_vram_gb,
            )

            if not released:
                return False

        self.state_manager.cancel(job)

        return True
