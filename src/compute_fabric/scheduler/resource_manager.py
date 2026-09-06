from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.gpu.gpu_inventory import GPU
from compute_fabric.jobs.job_manager import Job


class ResourceManager:
    def __init__(self, gpu_manager: GPUManager) -> None:
        self.gpu_manager = gpu_manager

    def get_eligible_gpus(self, job: Job) -> list[GPU]:
        eligible_gpus = []

        for gpu in self.gpu_manager.get_available_gpus():
            if job.gpu_type is not None and gpu.gpu_type != job.gpu_type:
                continue

            if not gpu.has_vram(job.min_vram_gb):
                continue

            eligible_gpus.append(gpu)

        return eligible_gpus
