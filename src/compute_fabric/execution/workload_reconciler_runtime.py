import logging
from collections.abc import Callable

from compute_fabric.execution.workload_reconciler import WorkloadReconciler


logger = logging.getLogger(__name__)


class WorkloadReconcilerRuntime:
    def __init__(
        self,
        reconciler: WorkloadReconciler,
        interval_seconds: float,
        wait: Callable[[float], bool],
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        self.reconciler = reconciler
        self.interval_seconds = interval_seconds
        self.wait = wait

    def run(self) -> None:
        while True:
            try:
                self.reconciler.reconcile_once()
            except Exception:
                logger.exception(
                    "workload_reconciliation_pass_failed"
                )

            if self.wait(self.interval_seconds):
                return
