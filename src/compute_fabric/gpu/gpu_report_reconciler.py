from compute_fabric.common.enums import GPUStatus
from compute_fabric.gpu.gpu_inventory import GPU
from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.gpu.gpu_report import GPUReport


class GPUReportReconciler:
    def __init__(self, gpu_manager: GPUManager) -> None:
        self.gpu_manager = gpu_manager

    def reconcile(self, report: GPUReport) -> GPU:
        gpu = self.gpu_manager.get_gpu(report.gpu_id)

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
