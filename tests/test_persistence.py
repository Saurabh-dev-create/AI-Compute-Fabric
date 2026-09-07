from compute_fabric.common.enums import JobStatus
from compute_fabric.execution.workload_spec import WorkloadSpec
from compute_fabric.jobs.job_manager import Job
from compute_fabric.storage.postgres_repository import PostgresJobRepository


DATABASE_URL = (
    "postgresql://compute_fabric:"
    "compute_fabric_dev@localhost:5432/compute_fabric"
)


def test_save_and_get_job():
    repository = PostgresJobRepository(DATABASE_URL)

    job = Job(
        id="persist-test-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=10,
        status=JobStatus.SCHEDULED,
        gpu_id="gpu-001",
        node_id="gpu-node-01",
        allocated_vram_gb=40,
        workload_id="compute-fabric-persist-test-001",
        workload_spec=WorkloadSpec(
            image="nvidia/cuda:12.8.1-base-ubuntu24.04",
            command=("sh", "-c"),
            args=("nvidia-smi",),
        ),
    )

    repository.save(job)

    restored = repository.get(job.id)

    assert restored is not None
    assert restored.id == job.id
    assert restored.job_type == job.job_type
    assert restored.gpu_type == job.gpu_type
    assert restored.min_vram_gb == job.min_vram_gb
    assert restored.priority == job.priority
    assert restored.status == JobStatus.SCHEDULED
    assert restored.gpu_id == "gpu-001"
    assert restored.node_id == "gpu-node-01"
    assert restored.allocated_vram_gb == 40
    assert restored.workload_id == "compute-fabric-persist-test-001"
    assert restored.workload_spec == WorkloadSpec(
        image="nvidia/cuda:12.8.1-base-ubuntu24.04",
        command=("sh", "-c"),
        args=("nvidia-smi",),
    )

    repository.delete(job.id)


def test_update_existing_job():
    repository = PostgresJobRepository(DATABASE_URL)

    job = Job(
        id="persist-test-002",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=20,
        priority=5,
    )

    repository.save(job)

    job.status = JobStatus.RUNNING
    job.gpu_id = "gpu-001"
    job.node_id = "gpu-node-01"
    job.allocated_vram_gb = 20
    job.workload_id = "compute-fabric-persist-test-002"
    job.workload_spec = WorkloadSpec(
        image="example/training:v2",
        command=("python",),
        args=("train.py", "--epochs", "2"),
    )

    repository.save(job)

    restored = repository.get(job.id)

    assert restored is not None
    assert restored.status == JobStatus.RUNNING
    assert restored.gpu_id == "gpu-001"
    assert restored.node_id == "gpu-node-01"
    assert restored.allocated_vram_gb == 20
    assert restored.workload_id == "compute-fabric-persist-test-002"
    assert restored.workload_spec == WorkloadSpec(
        image="example/training:v2",
        command=("python",),
        args=("train.py", "--epochs", "2"),
    )

    repository.delete(job.id)


def test_delete_job():
    repository = PostgresJobRepository(DATABASE_URL)

    job = Job(
        id="persist-test-003",
        job_type="inference",
        gpu_type="T4",
        min_vram_gb=8,
        priority=1,
    )

    repository.save(job)

    assert repository.get(job.id) is not None

    repository.delete(job.id)

    assert repository.get(job.id) is None
