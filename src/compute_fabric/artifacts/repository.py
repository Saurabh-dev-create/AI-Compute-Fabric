from abc import ABC, abstractmethod

from compute_fabric.artifacts.artifact import ModelArtifact


class ArtifactRepository(ABC):
    @abstractmethod
    def save(self, artifact: ModelArtifact) -> None:
        pass

    @abstractmethod
    def get(self, artifact_id: str) -> ModelArtifact | None:
        pass

    @abstractmethod
    def list_by_job(self, job_id: str) -> list[ModelArtifact]:
        pass
