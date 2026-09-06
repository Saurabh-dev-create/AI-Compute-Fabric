import pytest

from compute_fabric.api.main import gpu_manager, queue_manager
from compute_fabric.common.enums import GPUStatus


@pytest.fixture(autouse=True)
def reset_simulated_compute_state():
    gpu_defaults = {
        "gpu-001": {
            "free_vram_gb": 64,
            "status": GPUStatus.AVAILABLE,
        },
        "gpu-002": {
            "free_vram_gb": 45,
            "status": GPUStatus.AVAILABLE,
        },
        "gpu-003": {
            "free_vram_gb": 12,
            "status": GPUStatus.AVAILABLE,
        },
    }

    for gpu_id, defaults in gpu_defaults.items():
        gpu = gpu_manager.get_gpu(gpu_id)

        if gpu is None:
            raise RuntimeError(
                f"Expected simulated GPU {gpu_id} is missing"
            )

        gpu.free_vram_gb = defaults["free_vram_gb"]
        gpu.status = defaults["status"]

    while not queue_manager.is_empty():
        queue_manager.dequeue_job()

    yield

    while not queue_manager.is_empty():
        queue_manager.dequeue_job()
