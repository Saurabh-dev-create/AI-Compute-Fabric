from abc import ABC, abstractmethod
from pathlib import Path


class ArtifactStore(ABC):
    @abstractmethod
    def upload_directory(
        self,
        local_path: Path,
        artifact_key: str,
    ) -> str:
        """Upload an artifact directory and return its durable URI."""
        raise NotImplementedError
