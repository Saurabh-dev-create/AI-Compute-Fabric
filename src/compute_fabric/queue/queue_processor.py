from compute_fabric.jobs.job_state import JobStateManager
from compute_fabric.queue.queue_manager import QueueManager
from compute_fabric.scheduler.scheduler import Scheduler, SchedulingDecision


class QueueProcessor:
    def __init__(
        self,
        queue_manager: QueueManager,
        scheduler: Scheduler,
        state_manager: JobStateManager,
    ) -> None:
        self.queue_manager = queue_manager
        self.scheduler = scheduler
        self.state_manager = state_manager

    def process_next(self) -> SchedulingDecision | None:
        job = self.queue_manager.peek_next_job()

        if job is None:
            return None

        decision = self.scheduler.schedule(job)

        if decision is None:
            return None

        self.queue_manager.dequeue_job()

        job.gpu_id = decision.gpu_id
        job.node_id = decision.node_id
        job.allocated_vram_gb = job.min_vram_gb

        self.state_manager.schedule(job)

        return decision
