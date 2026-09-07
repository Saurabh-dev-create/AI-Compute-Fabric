from datetime import UTC, datetime

from compute_fabric.gpu.gpu_agent import GPUAgent
from compute_fabric.gpu.gpu_report import GPUReport


def make_report(gpu_id: str) -> GPUReport:
    return GPUReport(
        gpu_id=gpu_id,
        gpu_type="T4",
        node_id="eks-gpu-node-01",
        total_vram_gb=16,
        free_vram_gb=12,
        utilization_percent=25,
        temperature_c=58,
        power_draw_watts=42,
        observed_at=datetime.now(UTC),
    )


class FakeCollector:
    def __init__(self, reports: list[GPUReport]) -> None:
        self.reports = reports
        self.collect_calls = 0

    def collect(self) -> list[GPUReport]:
        self.collect_calls += 1
        return self.reports


def test_run_once_collects_and_reports_each_gpu() -> None:
    reports = [
        make_report("GPU-aaa111"),
        make_report("GPU-bbb222"),
    ]
    collector = FakeCollector(reports)
    received: list[GPUReport] = []

    agent = GPUAgent(
        collector=collector,
        report_handler=received.append,
    )

    reported_count = agent.run_once()

    assert collector.collect_calls == 1
    assert reported_count == 2
    assert received == reports


def test_run_once_handles_empty_gpu_inventory() -> None:
    collector = FakeCollector([])
    received: list[GPUReport] = []

    agent = GPUAgent(
        collector=collector,
        report_handler=received.append,
    )

    reported_count = agent.run_once()

    assert collector.collect_calls == 1
    assert reported_count == 0
    assert received == []
