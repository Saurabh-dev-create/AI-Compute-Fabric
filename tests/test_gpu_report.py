from datetime import UTC, datetime

from compute_fabric.gpu.gpu_report import GPUReport


def test_gpu_report_captures_hardware_observation() -> None:
    observed_at = datetime.now(UTC)

    report = GPUReport(
        gpu_id="gpu-real-001",
        gpu_type="T4",
        node_id="eks-gpu-node-01",
        total_vram_gb=16,
        free_vram_gb=12,
        utilization_percent=25,
        temperature_c=58,
        power_draw_watts=42,
        observed_at=observed_at,
    )

    assert report.gpu_id == "gpu-real-001"
    assert report.gpu_type == "T4"
    assert report.node_id == "eks-gpu-node-01"
    assert report.total_vram_gb == 16
    assert report.free_vram_gb == 12
    assert report.utilization_percent == 25
    assert report.temperature_c == 58
    assert report.power_draw_watts == 42
    assert report.observed_at == observed_at
