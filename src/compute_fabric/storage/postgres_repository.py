from psycopg import Connection, connect
from psycopg.types.json import Jsonb

from compute_fabric.common.enums import JobStatus
from compute_fabric.execution.workload_spec import WorkloadSpec
from compute_fabric.jobs.job_manager import Job
from compute_fabric.storage.repository import JobRepository


class PostgresJobRepository(JobRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self) -> Connection:
        return connect(self.database_url)

    def save(self, job: Job) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO jobs (
                        id,
                        job_type,
                        gpu_type,
                        min_vram_gb,
                        priority,
                        status,
                        gpu_id,
                        node_id,
                        allocated_vram_gb,
                        workload_id,
                        workload_spec
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        job_type = EXCLUDED.job_type,
                        gpu_type = EXCLUDED.gpu_type,
                        min_vram_gb = EXCLUDED.min_vram_gb,
                        priority = EXCLUDED.priority,
                        status = EXCLUDED.status,
                        gpu_id = EXCLUDED.gpu_id,
                        node_id = EXCLUDED.node_id,
                        allocated_vram_gb = EXCLUDED.allocated_vram_gb,
                        workload_id = EXCLUDED.workload_id,
                        workload_spec = EXCLUDED.workload_spec
                    """,
                    (
                        job.id,
                        job.job_type,
                        job.gpu_type,
                        job.min_vram_gb,
                        job.priority,
                        job.status.value,
                        job.gpu_id,
                        job.node_id,
                        job.allocated_vram_gb,
                        job.workload_id,
                        (
                            Jsonb(
                                {
                                    "image": job.workload_spec.image,
                                    "command": list(job.workload_spec.command),
                                    "args": list(job.workload_spec.args),
                                }
                            )
                            if job.workload_spec is not None
                            else None
                        ),
                    ),
                )

    def get(self, job_id: str) -> Job | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        job_type,
                        gpu_type,
                        min_vram_gb,
                        priority,
                        status,
                        gpu_id,
                        node_id,
                        allocated_vram_gb,
                        workload_id,
                        workload_spec
                    FROM jobs
                    WHERE id = %s
                    """,
                    (job_id,),
                )

                row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def list_all(self) -> list[Job]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        job_type,
                        gpu_type,
                        min_vram_gb,
                        priority,
                        status,
                        gpu_id,
                        node_id,
                        allocated_vram_gb,
                        workload_id,
                        workload_spec
                    FROM jobs
                    ORDER BY id
                    """
                )

                rows = cursor.fetchall()

        return [self._row_to_job(row) for row in rows]

    def delete(self, job_id: str) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM jobs WHERE id = %s",
                    (job_id,),
                )

    @staticmethod
    def _row_to_job(row: tuple) -> Job:
        workload_data = row[10]

        workload_spec = (
            WorkloadSpec(
                image=workload_data["image"],
                command=tuple(workload_data.get("command", [])),
                args=tuple(workload_data.get("args", [])),
            )
            if workload_data is not None
            else None
        )

        return Job(
            id=row[0],
            job_type=row[1],
            gpu_type=row[2],
            min_vram_gb=row[3],
            priority=row[4],
            status=JobStatus(row[5]),
            gpu_id=row[6],
            node_id=row[7],
            allocated_vram_gb=row[8],
            workload_id=row[9],
            workload_spec=workload_spec,
        )
