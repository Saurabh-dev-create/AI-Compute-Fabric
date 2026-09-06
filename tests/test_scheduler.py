from compute_fabric.common.enums import GPUStatus
from compute_fabric.gpu.gpu_inventory import GPU, GPUInventory
from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.jobs.job_manager import Job
from compute_fabric.scheduler.resource_manager import ResourceManager
from compute_fabric.scheduler.scheduler import Scheduler
from compute_fabric.scheduler.scoring import GPUScorer


def create_scheduler() -> tuple[Scheduler, GPUManager]:
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

    scheduler = Scheduler(
        resource_manager,
        scorer,
        gpu_manager,
    )

    return scheduler, gpu_manager


def test_scheduler_selects_and_allocates_best_gpu():
    scheduler, gpu_manager = create_scheduler()

    job = Job(
        id="job-001",
        job_type="inference",
        gpu_type="A100",
        min_vram_gb=40,
        priority=3,
    )

    decision = scheduler.schedule(job)

    assert decision is not None
    assert decision.job_id == "job-001"
    assert decision.gpu_id == "gpu-001"
    assert decision.node_id == "gpu-node-01"
    assert decision.score == 1.1

    gpu = gpu_manager.get_gpu("gpu-001")

    assert gpu is not None
    assert gpu.free_vram_gb == 24
    assert gpu.status == GPUStatus.ALLOCATED


def test_scheduler_returns_none_when_no_gpu_is_eligible():
    scheduler, _ = create_scheduler()

    job = Job(
        id="job-002",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=100,
        priority=4,
    )

    decision = scheduler.schedule(job)

    assert decision is None


def test_scheduler_rejects_wrong_gpu_type():
    scheduler, _ = create_scheduler()

    job = Job(
        id="job-003",
        job_type="inference",
        gpu_type="H100",
        min_vram_gb=10,
        priority=2,
    )

    decision = scheduler.schedule(job)

    assert decision is None


def test_scheduler_does_not_reallocate_allocated_gpu():
    scheduler, gpu_manager = create_scheduler()

    job1 = Job(
        id="job-001",
        job_type="inference",
        gpu_type="A100",
        min_vram_gb=40,
        priority=3,
    )

    job2 = Job(
        id="job-002",
        job_type="inference",
        gpu_type="A100",
        min_vram_gb=40,
        priority=3,
    )

    decision1 = scheduler.schedule(job1)
    decision2 = scheduler.schedule(job2)

    assert decision1 is not None
    assert decision1.gpu_id == "gpu-001"

    assert decision2 is not None
    assert decision2.gpu_id == "gpu-002"

    gpu1 = gpu_manager.get_gpu("gpu-001")
    gpu2 = gpu_manager.get_gpu("gpu-002")

    assert gpu1 is not None
    assert gpu2 is not None

    assert gpu1.free_vram_gb == 24
    assert gpu2.free_vram_gb == 5
