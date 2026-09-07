import httpx

from compute_fabric.gpu.gpu_report import GPUReport


class HTTPGPUReportSender:
    def __init__(
        self,
        base_url: str,
        client: httpx.Client,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    def send(self, report: GPUReport) -> None:
        response = self.client.post(
            f"{self.base_url}/gpu/reports",
            json={
                "gpu_id": report.gpu_id,
                "gpu_type": report.gpu_type,
                "node_id": report.node_id,
                "total_vram_gb": report.total_vram_gb,
                "free_vram_gb": report.free_vram_gb,
                "utilization_percent": report.utilization_percent,
                "temperature_c": report.temperature_c,
                "power_draw_watts": report.power_draw_watts,
                "observed_at": report.observed_at.isoformat(),
            },
        )
        response.raise_for_status()
