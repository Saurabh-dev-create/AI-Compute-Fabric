import csv
from datetime import UTC, datetime
from io import StringIO

from compute_fabric.gpu.gpu_report import GPUReport


class NvidiaGPUCollector:
    def __init__(self, node_id: str) -> None:
        self.node_id = node_id

    def parse_output(self, output: str) -> list[GPUReport]:
        reports: list[GPUReport] = []

        reader = csv.reader(StringIO(output))

        for row in reader:
            if not row or all(not value.strip() for value in row):
                continue

            values = [value.strip() for value in row]

            if len(values) != 7:
                raise ValueError(
                    "Expected 7 fields from NVIDIA GPU query output"
                )

            (
                gpu_id,
                gpu_name,
                total_memory_mib,
                free_memory_mib,
                utilization_percent,
                temperature_c,
                power_draw_watts,
            ) = values

            reports.append(
                GPUReport(
                    gpu_id=gpu_id,
                    gpu_type=self._normalize_gpu_type(gpu_name),
                    node_id=self.node_id,
                    total_vram_gb=self._mib_to_gib(total_memory_mib),
                    free_vram_gb=self._mib_to_gib(free_memory_mib),
                    utilization_percent=float(utilization_percent),
                    temperature_c=float(temperature_c),
                    power_draw_watts=float(power_draw_watts),
                    observed_at=datetime.now(UTC),
                )
            )

        return reports

    @staticmethod
    def _mib_to_gib(value: str) -> float:
        return float(value) / 1024

    @staticmethod
    def _normalize_gpu_type(gpu_name: str) -> str:
        normalized = gpu_name.upper()

        if "A100" in normalized:
            return "A100"

        if "T4" in normalized:
            return "T4"

        return gpu_name.strip()
