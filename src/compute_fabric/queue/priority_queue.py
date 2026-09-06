import heapq

from compute_fabric.jobs.job_manager import Job


class PriorityJobQueue:
    def __init__(self) -> None:
        self._queue: list[tuple[int, int, Job]] = []
        self._sequence = 0

    def enqueue(self, job: Job) -> None:
        # Higher priority should be processed first.
        # heapq is a min-heap, so we store negative priority.
        heapq.heappush(
            self._queue,
            (-job.priority, self._sequence, job),
        )

        self._sequence += 1

    def dequeue(self) -> Job | None:
        if not self._queue:
            return None

        _, _, job = heapq.heappop(self._queue)
        return job

    def peek(self) -> Job | None:
        if not self._queue:
            return None

        _, _, job = self._queue[0]
        return job

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def size(self) -> int:
        return len(self._queue)
