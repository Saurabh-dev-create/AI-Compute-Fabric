from compute_fabric.jobs.job_manager import Job


class AdmissionController:
    def __init__(self, max_vram_gb: float = 80.0) -> None:
        self.max_vram_gb = max_vram_gb

    def admit(self, job: Job) -> bool:
        if job.min_vram_gb <= 0:
            return False

        if job.min_vram_gb > self.max_vram_gb:
            return False

        if job.priority < 0:
            return False

        return True
