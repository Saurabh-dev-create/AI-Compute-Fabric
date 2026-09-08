from psycopg import Connection, connect

from compute_fabric.artifacts.artifact import ModelArtifact
from compute_fabric.artifacts.repository import ArtifactRepository


class PostgresArtifactRepository(ArtifactRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self) -> Connection:
        return connect(self.database_url)

    def save(self, artifact: ModelArtifact) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO model_artifacts (
                        id,
                        job_id,
                        artifact_type,
                        storage_uri,
                        base_model,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        job_id = EXCLUDED.job_id,
                        artifact_type = EXCLUDED.artifact_type,
                        storage_uri = EXCLUDED.storage_uri,
                        base_model = EXCLUDED.base_model,
                        created_at = EXCLUDED.created_at
                    """,
                    (
                        artifact.id,
                        artifact.job_id,
                        artifact.artifact_type,
                        artifact.storage_uri,
                        artifact.base_model,
                        artifact.created_at,
                    ),
                )

    def get(self, artifact_id: str) -> ModelArtifact | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        job_id,
                        artifact_type,
                        storage_uri,
                        base_model,
                        created_at
                    FROM model_artifacts
                    WHERE id = %s
                    """,
                    (artifact_id,),
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_artifact(row)

    def list_by_job(self, job_id: str) -> list[ModelArtifact]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        job_id,
                        artifact_type,
                        storage_uri,
                        base_model,
                        created_at
                    FROM model_artifacts
                    WHERE job_id = %s
                    ORDER BY created_at ASC, id ASC
                    """,
                    (job_id,),
                )
                rows = cursor.fetchall()

        return [
            self._row_to_artifact(row)
            for row in rows
        ]

    @staticmethod
    def _row_to_artifact(row: tuple) -> ModelArtifact:
        return ModelArtifact(
            id=row[0],
            job_id=row[1],
            artifact_type=row[2],
            storage_uri=row[3],
            base_model=row[4],
            created_at=row[5],
        )
