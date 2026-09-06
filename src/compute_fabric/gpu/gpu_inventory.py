from dataclasses import dataclass

from compute_fabric.common.enums import GPUStatus


@dataclass
class GPU:
    id: str
    gpu_type: str
    total_vram_gb: float
    free_vram_gb: float
    utilization_percent: float
    temperature_c: float
    status: GPUStatus
    node_id: str

    def has_vram(self, required_vram_gb: float) -> bool:
        return self.free_vram_gb >= required_vram_gb

    def is_healthy(self) -> bool:
        return self.status != GPUStatus.UNHEALTHY


class GPUInventory:
    def __init__(self) -> None:
        self._gpus: dict[str, GPU] = {}

    def add_gpu(self, gpu: GPU) -> None:
        self._gpus[gpu.id] = gpu

    def remove_gpu(self, gpu_id: str) -> None:
        self._gpus.pop(gpu_id, None)

    def get_gpu(self, gpu_id: str) -> GPU | None:
        return self._gpus.get(gpu_id)

    def list_gpus(self) -> list[GPU]:
        return list(self._gpus.values())
