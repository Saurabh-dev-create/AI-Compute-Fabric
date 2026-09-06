from compute_fabric.common.enums import GPUStatus
from compute_fabric.gpu.gpu_inventory import GPU, GPUInventory


class GPUManager:
    def __init__(self, inventory: GPUInventory) -> None:
        self.inventory = inventory

    def register_gpu(self, gpu: GPU) -> None:
        self.inventory.add_gpu(gpu)

    def remove_gpu(self, gpu_id: str) -> None:
        self.inventory.remove_gpu(gpu_id)

    def get_gpu(self, gpu_id: str) -> GPU | None:
        return self.inventory.get_gpu(gpu_id)

    def list_gpus(self) -> list[GPU]:
        return self.inventory.list_gpus()

    def get_available_gpus(self) -> list[GPU]:
        return [
            gpu
            for gpu in self.inventory.list_gpus()
            if gpu.status == GPUStatus.AVAILABLE
            and gpu.is_healthy()
        ]

    def find_gpus_with_vram(self, required_vram_gb: float) -> list[GPU]:
        return [
            gpu
            for gpu in self.get_available_gpus()
            if gpu.has_vram(required_vram_gb)
        ]

    def allocate_gpu(self, gpu_id: str, required_vram_gb: float) -> bool:
        gpu = self.get_gpu(gpu_id)

        if gpu is None:
            return False

        if gpu.status != GPUStatus.AVAILABLE:
            return False

        if not gpu.is_healthy():
            return False

        if not gpu.has_vram(required_vram_gb):
            return False

        gpu.free_vram_gb -= required_vram_gb
        gpu.status = GPUStatus.ALLOCATED

        return True

    def release_gpu(self, gpu_id: str, released_vram_gb: float) -> bool:
        gpu = self.get_gpu(gpu_id)

        if gpu is None:
            return False

        gpu.free_vram_gb = min(
            gpu.total_vram_gb,
            gpu.free_vram_gb + released_vram_gb,
        )

        if gpu.free_vram_gb > 0:
            gpu.status = GPUStatus.AVAILABLE

        return True
