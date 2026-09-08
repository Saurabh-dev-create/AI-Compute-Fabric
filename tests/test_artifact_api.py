from uuid import uuid4

from fastapi.testclient import TestClient

from compute_fabric.api.main import (
    app,
    artifact_service,
    job_manager,
)


client = TestClient(app)


def _create_job(job_id: str) -> None:
    response = client.post(
        "/jobs",
        json={
            "job_id": job_id,
            "job_type": "training",
            "gpu_type": "T4",
            "min_vram_gb": 8,
            "priority": 1,
        },
    )

    assert response.status_code == 200


def test_register_and_get_artifact():
    suffix = uuid4().hex[:8]
    job_id = f"api-artifact-job-{suffix}"
    artifact_id = f"api-artifact-{suffix}"

    _create_job(job_id)

    try:
        response = client.post(
            "/artifacts",
            json={
                "artifact_id": artifact_id,
                "job_id": job_id,
                "artifact_type": "qlora_adapter",
                "storage_uri": (
                    "s3://test-artifacts/"
                    f"{job_id}/{artifact_id}/"
                ),
                "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["artifact_id"] == artifact_id
        assert data["job_id"] == job_id
        assert data["artifact_type"] == "qlora_adapter"
        assert data["storage_uri"] == (
            "s3://test-artifacts/"
            f"{job_id}/{artifact_id}/"
        )
        assert data["base_model"] == (
            "Qwen/Qwen2.5-0.5B-Instruct"
        )
        assert data["created_at"]

        response = client.get(
            f"/artifacts/{artifact_id}"
        )

        assert response.status_code == 200
        assert response.json()["artifact_id"] == artifact_id
        assert response.json()["job_id"] == job_id
    finally:
        artifact = artifact_service.get(artifact_id)

        if artifact is not None:
            with artifact_service._repository._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM model_artifacts WHERE id = %s",
                        (artifact_id,),
                    )

        job_manager.remove_job(job_id)


def test_list_artifacts_for_job():
    suffix = uuid4().hex[:8]
    job_id = f"api-artifact-list-job-{suffix}"
    artifact_id = f"api-artifact-list-{suffix}"

    _create_job(job_id)

    try:
        response = client.post(
            "/artifacts",
            json={
                "artifact_id": artifact_id,
                "job_id": job_id,
                "artifact_type": "qlora_adapter",
                "storage_uri": (
                    "s3://test-artifacts/"
                    f"{job_id}/{artifact_id}/"
                ),
                "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
            },
        )

        assert response.status_code == 201

        response = client.get(
            f"/jobs/{job_id}/artifacts"
        )

        assert response.status_code == 200

        artifacts = response.json()

        assert any(
            artifact["artifact_id"] == artifact_id
            for artifact in artifacts
        )
    finally:
        artifact = artifact_service.get(artifact_id)

        if artifact is not None:
            with artifact_service._repository._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM model_artifacts WHERE id = %s",
                        (artifact_id,),
                    )

        job_manager.remove_job(job_id)


def test_get_missing_artifact_returns_404():
    artifact_id = f"missing-artifact-{uuid4().hex}"

    response = client.get(
        f"/artifacts/{artifact_id}"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Artifact not found"
    }
