from pathlib import Path

from compute_fabric.artifacts.store import ArtifactStore


class S3ArtifactStore(ArtifactStore):
    def __init__(self, s3_client: object, bucket: str) -> None:
        self._s3_client = s3_client
        self._bucket = bucket

    def upload_directory(
        self,
        local_path: Path,
        artifact_key: str,
    ) -> str:
        if not local_path.is_dir():
            raise ValueError(
                f"Artifact directory does not exist: {local_path}"
            )

        files = sorted(
            path
            for path in local_path.rglob("*")
            if path.is_file()
        )

        if not files:
            raise ValueError(
                f"Artifact directory is empty: {local_path}"
            )

        prefix = artifact_key.strip("/")

        if not prefix:
            raise ValueError("artifact_key must not be empty")

        for path in files:
            relative_path = path.relative_to(local_path).as_posix()
            object_key = f"{prefix}/{relative_path}"

            self._s3_client.upload_file(
                str(path),
                self._bucket,
                object_key,
            )

        return f"s3://{self._bucket}/{prefix}/"
