from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ModelArtifact:
    id: str
    job_id: str
    artifact_type: str
    storage_uri: str
    base_model: str | None
    created_at: datetime
