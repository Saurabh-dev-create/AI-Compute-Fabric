from datetime import UTC, datetime

from compute_fabric.common.enums import GPUStatus
from compute_fabric.gpu.gpu_inventory import GPUInventory
from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.gpu.gpu_report import GPUReport
from compute_fabric.gpu.gpu_report_reconciler import GPUReportReconciler


def make_report(
    *,
    free_vram_gb: float = 12,
    utilization_percent: float = 25,
    temperature_c: float = 58,
) -> GPUReport:
    return GPUReport(
        gpu_id="gpu-real-001",
        gpu_type="T4",
        node_id="eks-gpu-node-01",
        total_vram_gb=16,
        free_vram_gb=free_vram_gb,
        utilization_percent=utilization_percent,
        temperature_c=temperature_c,
        power_draw_watts=42,
        observed_at=datetime.now(UTC),
    )


def test_first_report_registers_real_gpu() -> None:
    manager = GPUManager(GPUInventory())
    reconciler = GPUReportReconciler(manager)

    gpu = reconciler.reconcile(make_report())

    assert gpu.id == "gpu-real-001"
    assert gpu.gpu_type == "T4"
    assert gpu.node_id == "eks-gpu-node-01"
    assert gpu.total_vram_gb == 16
    assert gpu.free_vram_gb == 12
    assert gpu.utilization_percent == 25
    assert gpu.temperature_c == 58
    assert gpu.status == GPUStatus.AVAILABLE

    assert manager.get_gpu("gpu-real-001") is gpu


def test_report_refreshes_observed_gpu_telemetry() -> None:
    manager = GPUManager(GPUInventory())
    reconciler = GPUReportReconciler(manager)

    reconciler.reconcile(make_report())

    gpu = reconciler.reconcile(
        make_report(
            free_vram_gb=10,
            utilization_percent=60,
            temperature_c=67,
        )
    )

    assert gpu.free_vram_gb == 10
    assert gpu.utilization_percent == 60
    assert gpu.temperature_c == 67


def test_report_does_not_erase_control_plane_allocation() -> None:
    manager = GPUManager(GPUInventory())
    reconciler = GPUReportReconciler(manager)

    reconciler.reconcile(make_report(free_vram_gb=16))

    assert manager.allocate_gpu("gpu-real-001", 8) is True

    gpu = manager.get_gpu("gpu-real-001")

    assert gpu is not None
    assert gpu.status == GPUStatus.ALLOCATED
    assert gpu.free_vram_gb == 8

    reconciler.reconcile(
        make_report(
            free_vram_gb=15,
            utilization_percent=40,
            temperature_c=62,
        )
    )

    assert gpu.status == GPUStatus.ALLOCATED
    assert gpu.free_vram_gb == 8
    assert gpu.utilization_percent == 40
    assert gpu.temperature_c == 62
