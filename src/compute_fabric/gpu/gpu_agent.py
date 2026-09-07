from collections.abc import Callable
from typing import Protocol

from compute_fabric.gpu.gpu_report import GPUReport


class GPUCollector(Protocol):
    def collect(self) -> list[GPUReport]:
        ...


class GPUAgent:
    def __init__(
        self,
        collector: GPUCollector,
        report_handler: Callable[[GPUReport], object],
    ) -> None:
        self.collector = collector
        self.report_handler = report_handler

    def run_once(self) -> int:
        reports = self.collector.collect()

        for report in reports:
            self.report_handler(report)

        return len(reports)
