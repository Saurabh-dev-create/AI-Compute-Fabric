from datetime import UTC, datetime

from compute_fabric.artifacts.artifact import ModelArtifact
from compute_fabric.artifacts.repository import ArtifactRepository
from compute_fabric.artifacts.service import ArtifactService


class InMemoryArtifactRepository(ArtifactRepository):
    def __init__(self) -> None:
        self.artifacts: dict[str, ModelArtifact] = {}

    def save(self, artifact: ModelArtifact) -> None:
        self.artifacts[artifact.id] = artifact

    def get(self, artifact_id: str) -> ModelArtifact | None:
        return self.artifacts.get(artifact_id)

    def list_by_job(self, job_id: str) -> list[ModelArtifact]:
        return [
            artifact
            for artifact in self.artifacts.values()
            if artifact.job_id == job_id
        ]


def _artifact(
    artifact_id: str = "artifact-001",
    job_id: str = "qlora-job-001",
) -> ModelArtifact:
    return ModelArtifact(
        id=artifact_id,
        job_id=job_id,
        artifact_type="qlora_adapter",
        storage_uri=(
            "s3://ai-compute-fabric-dev-artifacts/"
            f"{job_id}/{artifact_id}/"
        ),
        base_model="Qwen/Qwen2.5-0.5B",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )


def test_register_and_get_artifact() -> None:
    repository = InMemoryArtifactRepository()
    service = ArtifactService(repository)

    artifact = _artifact()
    service.register(artifact)

    assert service.get(artifact.id) == artifact


def test_list_artifacts_for_job() -> None:
    repository = InMemoryArtifactRepository()
    service = ArtifactService(repository)

    expected = _artifact()
    service.register(expected)
    service.register(
        _artifact(
            artifact_id="artifact-002",
            job_id="another-job",
        )
    )

    assert service.list_for_job("qlora-job-001") == [expected]
