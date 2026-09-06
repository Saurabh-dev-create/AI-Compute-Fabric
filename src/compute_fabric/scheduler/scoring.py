from compute_fabric.gpu.gpu_inventory import GPU
from compute_fabric.jobs.job_manager import Job


class GPUScorer:
    def score(self, gpu: GPU, job: Job) -> float:
        vram_score = self._vram_score(gpu, job)
        utilization_score = self._utilization_score(gpu)

        return vram_score + utilization_score

    def _vram_score(self, gpu: GPU, job: Job) -> float:
        if job.min_vram_gb <= 0:
            return 0.0

        headroom = gpu.free_vram_gb - job.min_vram_gb

        if headroom < 0:
            return 0.0

        return headroom / gpu.total_vram_gb

    def _utilization_score(self, gpu: GPU) -> float:
        return 1.0 - (gpu.utilization_percent / 100.0)
