from dataclasses import dataclass

from compute_fabric.gpu.gpu_inventory import GPU
from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.jobs.job_manager import Job
from compute_fabric.scheduler.resource_manager import ResourceManager
from compute_fabric.scheduler.scoring import GPUScorer


@dataclass
class SchedulingDecision:
    job_id: str
    gpu_id: str
    node_id: str
    score: float


class Scheduler:
    def __init__(
        self,
        resource_manager: ResourceManager,
        scorer: GPUScorer,
        gpu_manager: GPUManager,
    ) -> None:
        self.resource_manager = resource_manager
        self.scorer = scorer
        self.gpu_manager = gpu_manager

    def schedule(self, job: Job) -> SchedulingDecision | None:
        eligible_gpus = self.resource_manager.get_eligible_gpus(job)

        if not eligible_gpus:
            return None

        best_gpu: GPU | None = None
        best_score = float("-inf")

        for gpu in eligible_gpus:
            score = self.scorer.score(gpu, job)

            if score > best_score:
                best_score = score
                best_gpu = gpu

        if best_gpu is None:
            return None

        allocated = self.gpu_manager.allocate_gpu(
            best_gpu.id,
            job.min_vram_gb,
        )

        if not allocated:
            return None

        return SchedulingDecision(
            job_id=job.id,
            gpu_id=best_gpu.id,
            node_id=best_gpu.node_id,
            score=best_score,
        )
