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
