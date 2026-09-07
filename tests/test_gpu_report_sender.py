from datetime import UTC, datetime

import httpx
import pytest

from compute_fabric.gpu.gpu_report import GPUReport
from compute_fabric.gpu.gpu_report_sender import HTTPGPUReportSender


def make_report() -> GPUReport:
    return GPUReport(
        gpu_id="GPU-http-001",
        gpu_type="T4",
        node_id="eks-gpu-node-01",
        total_vram_gb=16,
        free_vram_gb=12,
        utilization_percent=25,
        temperature_c=58,
        power_draw_watts=42.5,
        observed_at=datetime(
            2026,
            9,
            7,
            12,
            0,
            tzinfo=UTC,
        ),
    )


def test_send_posts_gpu_report_to_control_plane() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request

        return httpx.Response(
            200,
            json={
                "gpu_id": "GPU-http-001",
                "status": "AVAILABLE",
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        sender = HTTPGPUReportSender(
            base_url="http://compute-fabric-api:8000",
            client=client,
        )

        sender.send(make_report())

    assert captured_request is not None
    assert captured_request.method == "POST"
    assert str(captured_request.url) == (
        "http://compute-fabric-api:8000/gpu/reports"
    )

    payload = __import__("json").loads(captured_request.content)

    assert payload == {
        "gpu_id": "GPU-http-001",
        "gpu_type": "T4",
        "node_id": "eks-gpu-node-01",
        "total_vram_gb": 16,
        "free_vram_gb": 12,
        "utilization_percent": 25,
        "temperature_c": 58,
        "power_draw_watts": 42.5,
        "observed_at": "2026-09-07T12:00:00+00:00",
    }


def test_send_raises_for_control_plane_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            request=request,
            json={"detail": "control plane unavailable"},
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        sender = HTTPGPUReportSender(
            base_url="http://compute-fabric-api:8000",
            client=client,
        )

        with pytest.raises(httpx.HTTPStatusError):
            sender.send(make_report())


def test_send_propagates_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "control plane connection failed",
            request=request,
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        sender = HTTPGPUReportSender(
            base_url="http://compute-fabric-api:8000",
            client=client,
        )

        with pytest.raises(httpx.ConnectError):
            sender.send(make_report())
