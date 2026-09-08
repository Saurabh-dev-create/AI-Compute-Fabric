from compute_fabric.artifacts.artifact import ModelArtifact
from compute_fabric.artifacts.repository import ArtifactRepository


class ArtifactService:
    def __init__(self, repository: ArtifactRepository) -> None:
        self._repository = repository

    def register(self, artifact: ModelArtifact) -> None:
        self._repository.save(artifact)

    def get(self, artifact_id: str) -> ModelArtifact | None:
        return self._repository.get(artifact_id)

    def list_for_job(self, job_id: str) -> list[ModelArtifact]:
        return self._repository.list_by_job(job_id)
