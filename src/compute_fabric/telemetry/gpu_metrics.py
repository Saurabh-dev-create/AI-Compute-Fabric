from compute_fabric.common.enums import GPUStatus
from compute_fabric.gpu.gpu_inventory import GPUInventory
from compute_fabric.telemetry.metrics import (
    GPU_FREE_VRAM_GB,
    GPU_STATUS,
    GPU_TEMPERATURE_CELSIUS,
    GPU_TOTAL_VRAM_GB,
    GPU_UTILIZATION_PERCENT,
)


def update_gpu_metrics(inventory: GPUInventory) -> None:
    for gpu in inventory.list_gpus():
        labels = {
            "gpu_id": gpu.id,
            "gpu_type": gpu.gpu_type,
            "node_id": gpu.node_id,
        }

        GPU_TOTAL_VRAM_GB.labels(**labels).set(gpu.total_vram_gb)
        GPU_FREE_VRAM_GB.labels(**labels).set(gpu.free_vram_gb)
        GPU_UTILIZATION_PERCENT.labels(**labels).set(
            gpu.utilization_percent
        )
        GPU_TEMPERATURE_CELSIUS.labels(**labels).set(
            gpu.temperature_c
        )

        for status in GPUStatus:
            GPU_STATUS.labels(
                **labels,
                status=status.value,
            ).set(
                1 if gpu.status == status else 0
            )
