from uuid import uuid4

from fastapi.testclient import TestClient

from compute_fabric.api.main import app


client = TestClient(app)


def test_metrics_endpoint() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "compute_fabric_job_submissions_total" in response.text
    assert "compute_fabric_scheduling_attempts_total" in response.text
    assert "compute_fabric_scheduling_latency_seconds" in response.text


def test_job_submission_updates_metrics() -> None:
    job_id = f"metrics-test-{uuid4()}"

    response = client.post(
        "/jobs",
        json={
            "job_id": job_id,
            "job_type": "inference",
            "gpu_type": "A100",
            "min_vram_gb": 8,
            "priority": 5,
        },
    )

    assert response.status_code == 200

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    assert "compute_fabric_job_submissions_total" in metrics_response.text
    assert (
        'compute_fabric_scheduling_results_total{result="scheduled"}'
        in metrics_response.text
    )
    assert (
        'compute_fabric_job_lifecycle_transitions_total{status="SCHEDULED"}'
        in metrics_response.text
    )

    start_response = client.post(f"/jobs/{job_id}/start")
    assert start_response.status_code == 200

    complete_response = client.post(f"/jobs/{job_id}/complete")
    assert complete_response.status_code == 200


def test_gpu_metrics_are_exposed() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "compute_fabric_gpu_total_vram_gb" in response.text
    assert "compute_fabric_gpu_free_vram_gb" in response.text
    assert "compute_fabric_gpu_utilization_percent" in response.text
    assert "compute_fabric_gpu_temperature_celsius" in response.text
    assert "compute_fabric_gpu_status" in response.text


def test_gpu_metrics_follow_allocation_lifecycle() -> None:
    job_id = f"gpu-metrics-{uuid4()}"

    before = client.get("/metrics")
    assert before.status_code == 200
    assert (
        'compute_fabric_gpu_free_vram_gb{gpu_id="gpu-001",'
        'gpu_type="A100",node_id="gpu-node-01"} 64.0'
        in before.text
    )

    response = client.post(
        "/jobs",
        json={
            "job_id": job_id,
            "job_type": "inference",
            "gpu_type": "A100",
            "min_vram_gb": 8,
            "priority": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "SCHEDULED"

    allocated = client.get("/metrics")

    assert (
        'compute_fabric_gpu_free_vram_gb{gpu_id="gpu-001",'
        'gpu_type="A100",node_id="gpu-node-01"} 56.0'
        in allocated.text
    )
    assert (
        'status="ALLOCATED"} 1.0'
        in allocated.text
    )

    start_response = client.post(f"/jobs/{job_id}/start")
    assert start_response.status_code == 200

    complete_response = client.post(f"/jobs/{job_id}/complete")
    assert complete_response.status_code == 200

    released = client.get("/metrics")

    assert (
        'compute_fabric_gpu_free_vram_gb{gpu_id="gpu-001",'
        'gpu_type="A100",node_id="gpu-node-01"} 64.0'
        in released.text
    )
    assert (
        'status="AVAILABLE"} 1.0'
        in released.text
    )
