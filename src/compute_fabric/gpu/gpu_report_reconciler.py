from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from compute_fabric.common.enums import GPUStatus
from compute_fabric.gpu.gpu_inventory import GPU
from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.gpu.gpu_report import GPUReport


class GPUReportReconciler:
    def __init__(
        self,
        gpu_manager: GPUManager,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.gpu_manager = gpu_manager
        self.now = now or (lambda: datetime.now(UTC))
        self._last_seen_at: dict[str, datetime] = {}

    def reconcile(self, report: GPUReport) -> GPU:
        gpu = self.gpu_manager.get_gpu(report.gpu_id)

        # Liveness is based on when the control plane receives the
        # report, not the worker node's telemetry clock.
        self._last_seen_at[report.gpu_id] = self.now()

        if gpu is None:
            gpu = GPU(
                id=report.gpu_id,
                gpu_type=report.gpu_type,
                total_vram_gb=report.total_vram_gb,
                free_vram_gb=report.free_vram_gb,
                utilization_percent=report.utilization_percent,
                temperature_c=report.temperature_c,
                status=GPUStatus.AVAILABLE,
                node_id=report.node_id,
            )

            self.gpu_manager.register_gpu(gpu)
            return gpu

        gpu.gpu_type = report.gpu_type
        gpu.node_id = report.node_id
        gpu.total_vram_gb = report.total_vram_gb
        gpu.utilization_percent = report.utilization_percent
        gpu.temperature_c = report.temperature_c

        if gpu.status == GPUStatus.AVAILABLE:
            gpu.free_vram_gb = report.free_vram_gb

        return gpu

    def expire_stale(
        self,
        *,
        now: datetime,
        stale_after_seconds: float,
    ) -> int:
        if stale_after_seconds <= 0:
            raise ValueError(
                "stale_after_seconds must be greater than zero"
            )

        stale_before = now - timedelta(seconds=stale_after_seconds)
        expired = 0

        for gpu_id, last_seen_at in list(
            self._last_seen_at.items()
        ):
            gpu = self.gpu_manager.get_gpu(gpu_id)

            if gpu is None:
                self._last_seen_at.pop(gpu_id, None)
                continue

            # Never discard an active control-plane reservation merely
            # because hardware telemetry temporarily stopped.
            if gpu.status != GPUStatus.AVAILABLE:
                continue

            if last_seen_at > stale_before:
                continue

            self.gpu_manager.remove_gpu(gpu_id)
            self._last_seen_at.pop(gpu_id, None)
            expired += 1

        return expired
