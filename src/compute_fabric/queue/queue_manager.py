from compute_fabric.jobs.job_manager import Job
from compute_fabric.queue.admission import AdmissionController
from compute_fabric.queue.priority_queue import PriorityJobQueue


class QueueManager:
    def __init__(
        self,
        queue: PriorityJobQueue,
        admission_controller: AdmissionController,
    ) -> None:
        self.queue = queue
        self.admission_controller = admission_controller

    def submit_job(self, job: Job) -> bool:
        if not self.admission_controller.admit(job):
            return False

        self.queue.enqueue(job)
        return True

    def enqueue_job(self, job: Job) -> None:
        self.queue.enqueue(job)

    def dequeue_job(self) -> Job | None:
        return self.queue.dequeue()

    def peek_next_job(self) -> Job | None:
        return self.queue.peek()

    def queue_size(self) -> int:
        return self.queue.size()

    def is_empty(self) -> bool:
        return self.queue.is_empty()
