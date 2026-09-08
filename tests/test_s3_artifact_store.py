from pathlib import Path

import pytest

from compute_fabric.artifacts.s3_store import S3ArtifactStore


class FakeS3Client:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []

    def upload_file(
        self,
        filename: str,
        bucket: str,
        key: str,
    ) -> None:
        self.uploads.append((filename, bucket, key))


def test_upload_directory_preserves_relative_paths(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "adapter"
    nested_dir = artifact_dir / "nested"
    nested_dir.mkdir(parents=True)

    (artifact_dir / "adapter_config.json").write_text("{}")
    (nested_dir / "weights.bin").write_bytes(b"weights")

    client = FakeS3Client()
    store = S3ArtifactStore(
        s3_client=client,
        bucket="compute-fabric-artifacts",
    )

    uri = store.upload_directory(
        artifact_dir,
        "jobs/job-001/artifacts/artifact-001",
    )

    assert uri == (
        "s3://compute-fabric-artifacts/"
        "jobs/job-001/artifacts/artifact-001/"
    )

    uploaded_keys = {
        upload[2]
        for upload in client.uploads
    }

    assert uploaded_keys == {
        (
            "jobs/job-001/artifacts/artifact-001/"
            "adapter_config.json"
        ),
        (
            "jobs/job-001/artifacts/artifact-001/"
            "nested/weights.bin"
        ),
    }


def test_upload_directory_rejects_missing_directory(
    tmp_path: Path,
) -> None:
    store = S3ArtifactStore(
        s3_client=FakeS3Client(),
        bucket="compute-fabric-artifacts",
    )

    with pytest.raises(ValueError, match="does not exist"):
        store.upload_directory(
            tmp_path / "missing",
            "jobs/job-001/artifacts/artifact-001",
        )


def test_upload_directory_rejects_empty_directory(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "adapter"
    artifact_dir.mkdir()

    store = S3ArtifactStore(
        s3_client=FakeS3Client(),
        bucket="compute-fabric-artifacts",
    )

    with pytest.raises(ValueError, match="empty"):
        store.upload_directory(
            artifact_dir,
            "jobs/job-001/artifacts/artifact-001",
        )
