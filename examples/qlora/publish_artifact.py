import json
import os
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen


ARTIFACT_TYPE = "qlora_adapter"


def upload_directory(
    *,
    s3_client: object,
    local_path: Path,
    bucket: str,
    prefix: str,
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

    normalized_prefix = prefix.strip("/")

    if not normalized_prefix:
        raise ValueError("Artifact prefix must not be empty")

    for path in files:
        relative_path = path.relative_to(
            local_path
        ).as_posix()

        object_key = (
            f"{normalized_prefix}/{relative_path}"
        )

        s3_client.upload_file(
            str(path),
            bucket,
            object_key,
        )

    return (
        f"s3://{bucket}/{normalized_prefix}/"
    )


def register_artifact(
    *,
    api_url: str,
    payload: dict[str, object],
    opener: Callable = urlopen,
) -> dict[str, object]:
    request = Request(
        f"{api_url.rstrip('/')}/artifacts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with opener(request, timeout=30) as response:
        body = response.read().decode("utf-8")

    return json.loads(body)


def publish_qlora_artifact(
    *,
    local_path: Path,
    base_model: str,
    environment: dict[str, str] | None = None,
    s3_client: object | None = None,
    opener: Callable = urlopen,
) -> dict[str, object]:
    env = environment or os.environ

    job_id = env.get(
        "COMPUTE_FABRIC_JOB_ID",
        "",
    ).strip()

    bucket = env.get(
        "COMPUTE_FABRIC_ARTIFACT_BUCKET",
        "",
    ).strip()

    api_url = env.get(
        "COMPUTE_FABRIC_API_URL",
        "",
    ).strip()

    if not job_id:
        raise RuntimeError(
            "COMPUTE_FABRIC_JOB_ID is not configured"
        )

    if not bucket:
        raise RuntimeError(
            "COMPUTE_FABRIC_ARTIFACT_BUCKET is not configured"
        )

    if not api_url:
        raise RuntimeError(
            "COMPUTE_FABRIC_API_URL is not configured"
        )

    artifact_id = f"{job_id}-qlora-adapter"
    prefix = f"{job_id}/{artifact_id}"

    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3")

    storage_uri = upload_directory(
        s3_client=s3_client,
        local_path=local_path,
        bucket=bucket,
        prefix=prefix,
    )

    payload = {
        "artifact_id": artifact_id,
        "job_id": job_id,
        "artifact_type": ARTIFACT_TYPE,
        "storage_uri": storage_uri,
        "base_model": base_model,
    }

    registered = register_artifact(
        api_url=api_url,
        payload=payload,
        opener=opener,
    )

    print(f"artifact_id={artifact_id}")
    print(f"artifact_uri={storage_uri}")
    print("ARTIFACT_PUBLICATION_COMPLETED")

    return registered
