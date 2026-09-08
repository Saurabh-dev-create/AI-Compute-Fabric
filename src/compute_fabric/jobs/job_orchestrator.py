from compute_fabric.common.enums import JobStatus
from compute_fabric.execution.workload_observer import (
    WorkloadObserver,
    WorkloadRuntimeStatus,
)
from compute_fabric.execution.workload_runner import (
    WorkloadExecution,
    WorkloadRunner,
)
from compute_fabric.execution.workload_spec import WorkloadSpec
from compute_fabric.execution.workload_terminator import WorkloadTerminator
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
        workload_runner: WorkloadRunner | None = None,
        workload_observer: WorkloadObserver | None = None,
        workload_terminator: WorkloadTerminator | None = None,
    ) -> None:
        self.job_manager = job_manager
        self.queue_manager = queue_manager
        self.queue_processor = queue_processor
        self.scheduler = scheduler
        self.state_manager = state_manager
        self.gpu_manager = gpu_manager
        self.workload_runner = workload_runner
        self.workload_observer = workload_observer
        self.workload_terminator = workload_terminator

    def submit_and_schedule(self, job: Job) -> SchedulingDecision | None:
        self.job_manager.submit_job(job)       

        if not self.queue_manager.submit_job(job):
            return None
        

        decision = self.queue_processor.process_next()

        if decision is not None:
            self.job_manager.update_job(job)

        return decision

    def launch_workload(
        self,
        job_id: str,
        decision: SchedulingDecision,
        spec: WorkloadSpec,
    ) -> WorkloadExecution | None:
        if self.workload_runner is None:
            raise RuntimeError("Workload runner is not configured")

        job = self.job_manager.get_job(job_id)

        if job is None:
            return None

        if (
            job.gpu_id != decision.gpu_id
            or job.node_id != decision.node_id
        ):
            raise ValueError(
                "Scheduling decision does not match persisted job placement"
            )

        try:
            execution = self.workload_runner.launch(
                job,
                decision,
                spec,
            )
        except Exception:
            self.fail_job(job_id)
            raise

        job.workload_id = execution.workload_id
        self.job_manager.update_job(job)

        return execution

    def reconcile_workload(self, job_id: str) -> bool:
        if self.workload_observer is None:
            raise RuntimeError("Workload observer is not configured")

        job = self.job_manager.get_job(job_id)

        if job is None or job.workload_id is None:
            return False

        if job.status in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }:
            return True

        execution_mode = (
            job.workload_spec.execution_mode
            if job.workload_spec is not None
            else "batch"
        )

        observation = self.workload_observer.observe(
            job.workload_id,
            execution_mode,
        )

        if observation.status == WorkloadRuntimeStatus.PENDING:
            return True

        if observation.status == WorkloadRuntimeStatus.RUNNING:
            if job.status == JobStatus.SCHEDULED:
                return self.start_job(job_id)

            return True

        if observation.status == WorkloadRuntimeStatus.SUCCEEDED:
            if job.status == JobStatus.SCHEDULED:
                if not self.start_job(job_id):
                    return False

            return self.complete_job(job_id)

        if observation.status == WorkloadRuntimeStatus.FAILED:
            return self.fail_job(job_id)

        return False

    def start_job(self, job_id: str) -> bool:
        job = self.job_manager.get_job(job_id)

        if job is None:
            return False

        self.state_manager.start(job)
        self.job_manager.update_job(job)

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
        self.job_manager.update_job(job)

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
        self.job_manager.update_job(job)

        return True

    def cancel_job(self, job_id: str) -> bool:
        job = self.job_manager.get_job(job_id)

        if job is None:
            return False

        if job.workload_id is not None:
            if self.workload_terminator is None:
                return False

            execution_mode = (
                job.workload_spec.execution_mode
                if job.workload_spec is not None
                else "batch"
            )

            self.workload_terminator.terminate(
                job.workload_id,
                execution_mode,
            )

        if job.gpu_id is not None:
            released = self.gpu_manager.release_gpu(
                job.gpu_id,
                job.allocated_vram_gb or job.min_vram_gb,
            )

            if not released:
                return False

        self.state_manager.cancel(job)
        self.job_manager.update_job(job)

        return True
