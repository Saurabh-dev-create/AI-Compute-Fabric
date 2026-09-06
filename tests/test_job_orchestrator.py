from compute_fabric.common.enums import GPUStatus, JobStatus
from compute_fabric.gpu.gpu_inventory import GPU, GPUInventory
from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.jobs.job_manager import Job, JobManager
from compute_fabric.jobs.job_orchestrator import JobOrchestrator
from compute_fabric.jobs.job_state import JobStateManager
from compute_fabric.queue.admission import AdmissionController
from compute_fabric.queue.priority_queue import PriorityJobQueue
from compute_fabric.queue.queue_manager import QueueManager
from compute_fabric.queue.queue_processor import QueueProcessor
from compute_fabric.scheduler.resource_manager import ResourceManager
from compute_fabric.scheduler.scheduler import Scheduler
from compute_fabric.scheduler.scoring import GPUScorer
from compute_fabric.storage.in_memory_repository import InMemoryJobRepository


def create_orchestrator() -> tuple[JobOrchestrator, GPUManager]:
    inventory = GPUInventory()
    gpu_manager = GPUManager(inventory)

    gpu_manager.register_gpu(
        GPU(
            id="gpu-001",
            gpu_type="A100",
            total_vram_gb=80,
            free_vram_gb=64,
            utilization_percent=20,
            temperature_c=55,
            status=GPUStatus.AVAILABLE,
            node_id="gpu-node-01",
        )
    )

    gpu_manager.register_gpu(
        GPU(
            id="gpu-002",
            gpu_type="A100",
            total_vram_gb=80,
            free_vram_gb=45,
            utilization_percent=75,
            temperature_c=65,
            status=GPUStatus.AVAILABLE,
            node_id="gpu-node-02",
        )
    )

    gpu_manager.register_gpu(
        GPU(
            id="gpu-003",
            gpu_type="T4",
            total_vram_gb=16,
            free_vram_gb=12,
            utilization_percent=10,
            temperature_c=50,
            status=GPUStatus.AVAILABLE,
            node_id="gpu-node-03",
        )
    )

    resource_manager = ResourceManager(gpu_manager)
    scorer = GPUScorer()
    scheduler = Scheduler(resource_manager, scorer, gpu_manager)

    admission_controller = AdmissionController(max_vram_gb=80)
    queue = PriorityJobQueue()
    queue_manager = QueueManager(queue, admission_controller)

    state_manager = JobStateManager()
    queue_processor = QueueProcessor(
        queue_manager,
        scheduler,
        state_manager,
    )
    repository = InMemoryJobRepository()
    job_manager = JobManager(repository)

    orchestrator = JobOrchestrator(
        job_manager,
        queue_manager,
        queue_processor,
        scheduler,
        state_manager,
        gpu_manager,
    )

    return orchestrator, gpu_manager


def test_submit_and_schedule_job():
    orchestrator, gpu_manager = create_orchestrator()

    job = Job(
        id="job-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    decision = orchestrator.submit_and_schedule(job)

    assert decision is not None
    assert decision.job_id == "job-001"
    assert decision.gpu_id == "gpu-001"

    assert job.status == JobStatus.SCHEDULED
    assert job.gpu_id == "gpu-001"
    assert job.node_id == "gpu-node-01"
    assert job.allocated_vram_gb == 40

    gpu = gpu_manager.get_gpu("gpu-001")

    assert gpu is not None
    assert gpu.free_vram_gb == 24
    assert gpu.status == GPUStatus.ALLOCATED


def test_complete_job_releases_gpu():
    orchestrator, gpu_manager = create_orchestrator()

    job = Job(
        id="job-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    orchestrator.submit_and_schedule(job)

    assert orchestrator.start_job("job-001") is True
    assert job.status == JobStatus.RUNNING

    assert orchestrator.complete_job("job-001") is True
    assert job.status == JobStatus.COMPLETED

    gpu = gpu_manager.get_gpu("gpu-001")

    assert gpu is not None
    assert gpu.free_vram_gb == 64
    assert gpu.status == GPUStatus.AVAILABLE


def test_fail_job_releases_gpu():
    orchestrator, gpu_manager = create_orchestrator()

    job = Job(
        id="job-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    orchestrator.submit_and_schedule(job)

    assert orchestrator.start_job("job-001") is True
    assert orchestrator.fail_job("job-001") is True

    assert job.status == JobStatus.FAILED

    gpu = gpu_manager.get_gpu("gpu-001")

    assert gpu is not None
    assert gpu.free_vram_gb == 64
    assert gpu.status == GPUStatus.AVAILABLE


def test_cancel_job_releases_gpu():
    orchestrator, gpu_manager = create_orchestrator()

    job = Job(
        id="job-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    orchestrator.submit_and_schedule(job)

    assert orchestrator.cancel_job("job-001") is True

    assert job.status == JobStatus.CANCELLED

    gpu = gpu_manager.get_gpu("gpu-001")

    assert gpu is not None
    assert gpu.free_vram_gb == 64
    assert gpu.status == GPUStatus.AVAILABLE


def test_unknown_job_returns_false():
    orchestrator, _ = create_orchestrator()

    assert orchestrator.start_job("job-999") is False
    assert orchestrator.complete_job("job-999") is False
    assert orchestrator.fail_job("job-999") is False
    assert orchestrator.cancel_job("job-999") is False


def test_rejected_job_is_not_scheduled():
    orchestrator, _ = create_orchestrator()

    job = Job(
        id="job-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=100,
        priority=5,
    )

    decision = orchestrator.submit_and_schedule(job)

    assert decision is None
    assert job.status == JobStatus.PENDING
    assert job.gpu_id is None
    assert job.node_id is None
