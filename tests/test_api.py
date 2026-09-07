import pytest
from fastapi.testclient import TestClient

from compute_fabric.api.main import app, job_manager


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def clean_api_test_jobs():
    for job in job_manager.list_jobs():
        if job.id.startswith("api-"):
            job_manager.remove_job(job.id)

    yield

    for job in job_manager.list_jobs():
        if job.id.startswith("api-"):
            job_manager.remove_job(job.id)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "AI Compute Fabric",
        "status": "running",
        "version": "0.1.0",
    }


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_endpoint():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_list_gpus():
    response = client.get("/gpus")

    assert response.status_code == 200

    gpus = response.json()

    assert len(gpus) == 3
    assert gpus[0]["id"] == "gpu-001"
    assert gpus[1]["id"] == "gpu-002"
    assert gpus[2]["id"] == "gpu-003"


def test_submit_job():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-job-001",
            "job_type": "inference",
            "gpu_type": "A100",
            "min_vram_gb": 20,
            "priority": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-job-001"
    assert data["status"] == "SCHEDULED"
    assert data["gpu_id"] is not None
    assert data["node_id"] is not None
    assert data["score"] is not None


def test_get_job():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-job-002",
            "job_type": "training",
            "gpu_type": "A100",
            "min_vram_gb": 10,
            "priority": 5,
        },
    )

    assert response.status_code == 200

    response = client.get("/jobs/api-job-002")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-job-002"
    assert data["status"] == "SCHEDULED"


def test_list_jobs():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-job-003",
            "job_type": "inference",
            "gpu_type": "T4",
            "min_vram_gb": 8,
            "priority": 1,
        },
    )

    assert response.status_code == 200

    response = client.get("/jobs")

    assert response.status_code == 200

    jobs = response.json()

    assert isinstance(jobs, list)
    assert any(job["job_id"] == "api-job-003" for job in jobs)


def test_start_job():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-job-004",
            "job_type": "training",
            "gpu_type": "A100",
            "min_vram_gb": 10,
            "priority": 5,
        },
    )

    assert response.status_code == 200

    response = client.post("/jobs/api-job-004/start")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-job-004"
    assert data["status"] == "RUNNING"


def test_complete_job():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-job-005",
            "job_type": "training",
            "gpu_type": "A100",
            "min_vram_gb": 10,
            "priority": 5,
        },
    )

    assert response.status_code == 200

    response = client.post("/jobs/api-job-005/complete")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-job-005"
    assert data["status"] == "COMPLETED"


def test_fail_job():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-job-006",
            "job_type": "training",
            "gpu_type": "A100",
            "min_vram_gb": 10,
            "priority": 5,
        },
    )

    assert response.status_code == 200

    response = client.post("/jobs/api-job-006/fail")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-job-006"
    assert data["status"] == "FAILED"


def test_cancel_job():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-job-007",
            "job_type": "inference",
            "gpu_type": "A100",
            "min_vram_gb": 10,
            "priority": 5,
        },
    )

    assert response.status_code == 200

    response = client.post("/jobs/api-job-007/cancel")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-job-007"
    assert data["status"] == "CANCELLED"


def test_unknown_job_returns_404():
    response = client.get("/jobs/non-existent-job")

    assert response.status_code == 404


def test_unknown_job_start_returns_404():
    response = client.post("/jobs/non-existent-job/start")

    assert response.status_code == 404


def test_unknown_job_complete_returns_404():
    response = client.post("/jobs/non-existent-job/complete")

    assert response.status_code == 404


def test_unknown_job_fail_returns_404():
    response = client.post("/jobs/non-existent-job/fail")

    assert response.status_code == 404


def test_unknown_job_cancel_returns_404():
    response = client.post("/jobs/non-existent-job/cancel")

    assert response.status_code == 404


def test_duplicate_job_returns_409():
    payload = {
        "job_id": "api-duplicate-job",
        "job_type": "inference",
        "gpu_type": "T4",
        "min_vram_gb": 4,
        "priority": 1,
    }

    first_response = client.post("/jobs", json=payload)

    assert first_response.status_code == 200

    second_response = client.post("/jobs", json=payload)

    assert second_response.status_code == 409


def test_job_rejected_when_vram_exceeds_admission_limit():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-rejected-job",
            "job_type": "training",
            "gpu_type": "A100",
            "min_vram_gb": 100,
            "priority": 10,
        },
    )

    assert response.status_code == 400


def test_wrong_gpu_type_results_in_pending_job():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-wrong-gpu-job",
            "job_type": "training",
            "gpu_type": "H100",
            "min_vram_gb": 20,
            "priority": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-wrong-gpu-job"
    assert data["status"] == "PENDING"
    assert data["gpu_id"] is None
    assert data["node_id"] is None


def test_job_rejects_negative_vram():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-invalid-vram",
            "job_type": "training",
            "gpu_type": "A100",
            "min_vram_gb": -10,
            "priority": 10,
        },
    )

    assert response.status_code == 422


def test_job_rejects_negative_priority():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-invalid-priority",
            "job_type": "training",
            "gpu_type": "A100",
            "min_vram_gb": 20,
            "priority": -1,
        },
    )

    assert response.status_code == 422


def test_gpu_report_registers_gpu_in_control_plane() -> None:
    report = {
        "gpu_id": "GPU-api-real-001",
        "gpu_type": "T4",
        "node_id": "eks-gpu-node-api-test",
        "total_vram_gb": 16,
        "free_vram_gb": 12,
        "utilization_percent": 25,
        "temperature_c": 58,
        "power_draw_watts": 42.5,
        "observed_at": "2026-09-07T12:00:00Z",
    }

    response = client.post("/gpu/reports", json=report)

    assert response.status_code == 200

    body = response.json()

    assert body["gpu_id"] == "GPU-api-real-001"
    assert body["status"] == "AVAILABLE"

    gpus_response = client.get("/gpus")

    assert gpus_response.status_code == 200

    gpu = next(
        item
        for item in gpus_response.json()
        if item["id"] == "GPU-api-real-001"
    )

    assert gpu["gpu_type"] == "T4"
    assert gpu["node_id"] == "eks-gpu-node-api-test"
    assert gpu["total_vram_gb"] == 16
    assert gpu["free_vram_gb"] == 12


def test_gpu_report_rejects_invalid_vram() -> None:
    response = client.post(
        "/gpu/reports",
        json={
            "gpu_id": "GPU-api-invalid",
            "gpu_type": "T4",
            "node_id": "eks-gpu-node-api-test",
            "total_vram_gb": 16,
            "free_vram_gb": -1,
            "utilization_percent": 25,
            "temperature_c": 58,
            "power_draw_watts": 42.5,
            "observed_at": "2026-09-07T12:00:00Z",
        },
    )

    assert response.status_code == 422


def test_submit_job_persists_workload_spec():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-workload-job-001",
            "job_type": "inference",
            "gpu_type": "T4",
            "min_vram_gb": 4,
            "priority": 5,
            "workload": {
                "image": "nvidia/cuda:12.8.1-base-ubuntu24.04",
                "command": ["sh", "-c"],
                "args": ["nvidia-smi"],
            },
        },
    )

    assert response.status_code == 200

    stored_job = job_manager.get_job("api-workload-job-001")

    assert stored_job is not None
    assert stored_job.workload_spec is not None
    assert (
        stored_job.workload_spec.image
        == "nvidia/cuda:12.8.1-base-ubuntu24.04"
    )
    assert stored_job.workload_spec.command == ("sh", "-c")
    assert stored_job.workload_spec.args == ("nvidia-smi",)


def test_submit_job_rejects_empty_workload_image():
    response = client.post(
        "/jobs",
        json={
            "job_id": "api-workload-invalid-image",
            "job_type": "inference",
            "gpu_type": "T4",
            "min_vram_gb": 4,
            "priority": 5,
            "workload": {
                "image": "",
                "command": [],
                "args": [],
            },
        },
    )

    assert response.status_code == 422
