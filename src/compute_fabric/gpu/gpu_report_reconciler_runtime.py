import logging
from collections.abc import Callable
from datetime import datetime

from compute_fabric.gpu.gpu_report_reconciler import GPUReportReconciler


logger = logging.getLogger(__name__)


class GPUReportReconcilerRuntime:
    def __init__(
        self,
        reconciler: GPUReportReconciler,
        *,
        stale_after_seconds: float,
        interval_seconds: float,
        now: Callable[[], datetime],
        wait: Callable[[float], bool],
    ) -> None:
        if stale_after_seconds <= 0:
            raise ValueError(
                "stale_after_seconds must be greater than zero"
            )

        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        self.reconciler = reconciler
        self.stale_after_seconds = stale_after_seconds
        self.interval_seconds = interval_seconds
        self.now = now
        self.wait = wait

    def run(self) -> None:
        while True:
            try:
                self.reconciler.expire_stale(
                    now=self.now(),
                    stale_after_seconds=self.stale_after_seconds,
                )
            except Exception:
                logger.exception(
                    "gpu_stale_reconciliation_pass_failed"
                )

            if self.wait(self.interval_seconds):
                return
