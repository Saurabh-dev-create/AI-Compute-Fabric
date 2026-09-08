import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory


MODULE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "qlora"
    / "publish_artifact.py"
)

spec = importlib.util.spec_from_file_location(
    "qlora_publish_artifact",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeS3Client:
    def __init__(self) -> None:
        self.uploads: list[
            tuple[str, str, str]
        ] = []

    def upload_file(
        self,
        filename: str,
        bucket: str,
        key: str,
    ) -> None:
        self.uploads.append(
            (filename, bucket, key)
        )


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, object],
    ) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            self._payload
        ).encode("utf-8")


def test_publish_qlora_artifact_uploads_and_registers():
    s3_client = FakeS3Client()
    captured: dict[str, object] = {}

    def opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(
            request.data.decode("utf-8")
        )

        return FakeResponse(
            {
                "artifact_id": (
                    "training-001-qlora-adapter"
                )
            }
        )

    with TemporaryDirectory() as tmp:
        artifact_dir = Path(tmp)

        (artifact_dir / "adapter_config.json").write_text(
            "{}"
        )

        nested = artifact_dir / "tokenizer"
        nested.mkdir()

        (nested / "tokenizer.json").write_text(
            "{}"
        )

        result = module.publish_qlora_artifact(
            local_path=artifact_dir,
            base_model=(
                "Qwen/Qwen2.5-0.5B-Instruct"
            ),
            environment={
                "COMPUTE_FABRIC_JOB_ID": (
                    "training-001"
                ),
                "COMPUTE_FABRIC_ARTIFACT_BUCKET": (
                    "artifact-bucket"
                ),
                "COMPUTE_FABRIC_API_URL": (
                    "http://compute-fabric-api:8000"
                ),
            },
            s3_client=s3_client,
            opener=opener,
        )

    assert result["artifact_id"] == (
        "training-001-qlora-adapter"
    )

    assert [
        upload[2]
        for upload in s3_client.uploads
    ] == [
        (
            "training-001/"
            "training-001-qlora-adapter/"
            "adapter_config.json"
        ),
        (
            "training-001/"
            "training-001-qlora-adapter/"
            "tokenizer/tokenizer.json"
        ),
    ]

    assert captured["url"] == (
        "http://compute-fabric-api:8000/artifacts"
    )

    assert captured["payload"] == {
        "artifact_id": (
            "training-001-qlora-adapter"
        ),
        "job_id": "training-001",
        "artifact_type": "qlora_adapter",
        "storage_uri": (
            "s3://artifact-bucket/"
            "training-001/"
            "training-001-qlora-adapter/"
        ),
        "base_model": (
            "Qwen/Qwen2.5-0.5B-Instruct"
        ),
    }


def test_publish_requires_runtime_context():
    with TemporaryDirectory() as tmp:
        artifact_dir = Path(tmp)
        (artifact_dir / "adapter.json").write_text(
            "{}"
        )

        try:
            module.publish_qlora_artifact(
                local_path=artifact_dir,
                base_model="model",
                environment={},
                s3_client=FakeS3Client(),
            )
        except RuntimeError as exc:
            assert (
                "COMPUTE_FABRIC_JOB_ID"
                in str(exc)
            )
        else:
            raise AssertionError(
                "Expected RuntimeError"
            )
