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


class FakeWorkloadRunner:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = []

    def launch(self, job, decision, spec):
        from compute_fabric.execution.workload_runner import WorkloadExecution

        self.calls.append((job, decision, spec))

        if self.should_fail:
            raise RuntimeError("workload launch failed")

        return WorkloadExecution(
            job_id=job.id,
            workload_id=f"compute-fabric-{job.id}",
            node_id=decision.node_id,
        )


def create_orchestrator_with_runner(
    runner,
) -> tuple[JobOrchestrator, GPUManager]:
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
        workload_runner=runner,
    )

    return orchestrator, gpu_manager


def test_launch_workload_persists_execution_identity():
    from compute_fabric.execution.workload_spec import WorkloadSpec

    runner = FakeWorkloadRunner()
    orchestrator, _ = create_orchestrator_with_runner(runner)

    job = Job(
        id="job-execution-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    decision = orchestrator.submit_and_schedule(job)

    assert decision is not None

    execution = orchestrator.launch_workload(
        job.id,
        decision,
        WorkloadSpec(
            image="nvidia/cuda:12.8.1-base-ubuntu24.04",
            command=("sh", "-c"),
            args=("nvidia-smi",),
        ),
    )

    assert execution is not None
    assert execution.workload_id == "compute-fabric-job-execution-001"

    stored_job = orchestrator.job_manager.get_job(job.id)

    assert stored_job is not None
    assert stored_job.status == JobStatus.SCHEDULED
    assert stored_job.workload_id == "compute-fabric-job-execution-001"
    assert len(runner.calls) == 1


def test_launch_failure_releases_gpu_and_fails_job():
    from compute_fabric.execution.workload_spec import WorkloadSpec

    runner = FakeWorkloadRunner(should_fail=True)
    orchestrator, gpu_manager = create_orchestrator_with_runner(runner)

    job = Job(
        id="job-execution-002",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    decision = orchestrator.submit_and_schedule(job)

    assert decision is not None

    gpu = gpu_manager.get_gpu("gpu-001")

    assert gpu is not None
    assert gpu.status == GPUStatus.ALLOCATED
    assert gpu.free_vram_gb == 24

    import pytest

    with pytest.raises(RuntimeError, match="workload launch failed"):
        orchestrator.launch_workload(
            job.id,
            decision,
            WorkloadSpec(
                image="nvidia/cuda:12.8.1-base-ubuntu24.04",
                command=("sh", "-c"),
                args=("nvidia-smi",),
            ),
        )

    stored_job = orchestrator.job_manager.get_job(job.id)

    assert stored_job is not None
    assert stored_job.status == JobStatus.FAILED
    assert stored_job.workload_id is None

    assert gpu.status == GPUStatus.AVAILABLE
    assert gpu.free_vram_gb == 64


def test_launch_rejects_mismatched_scheduling_decision():
    import pytest

    from compute_fabric.execution.workload_spec import WorkloadSpec
    from compute_fabric.scheduler.scheduler import SchedulingDecision

    runner = FakeWorkloadRunner()
    orchestrator, _ = create_orchestrator_with_runner(runner)

    job = Job(
        id="job-execution-003",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    decision = orchestrator.submit_and_schedule(job)

    assert decision is not None

    wrong_decision = SchedulingDecision(
        job_id=job.id,
        gpu_id=decision.gpu_id,
        node_id="wrong-node",
        score=decision.score,
    )

    with pytest.raises(
        ValueError,
        match="Scheduling decision does not match persisted job placement",
    ):
        orchestrator.launch_workload(
            job.id,
            wrong_decision,
            WorkloadSpec(image="example/image:latest"),
        )

    assert runner.calls == []


class FakeWorkloadObserver:
    def __init__(self, status):
        self.status = status
        self.calls = []

    def observe(self, workload_id):
        from compute_fabric.execution.workload_observer import (
            WorkloadObservation,
        )

        self.calls.append(workload_id)

        return WorkloadObservation(
            workload_id=workload_id,
            status=self.status,
        )


def create_orchestrator_with_observer(observer):
    orchestrator, gpu_manager = create_orchestrator()
    orchestrator.workload_observer = observer
    return orchestrator, gpu_manager


def prepare_observed_job(orchestrator):
    job = Job(
        id="job-observed-001",
        job_type="training",
        gpu_type="A100",
        min_vram_gb=40,
        priority=5,
    )

    decision = orchestrator.submit_and_schedule(job)

    assert decision is not None

    job.workload_id = "compute-fabric-job-observed-001"
    orchestrator.job_manager.update_job(job)

    return job


def test_reconcile_pending_keeps_job_scheduled():
    from compute_fabric.execution.workload_observer import (
        WorkloadRuntimeStatus,
    )

    observer = FakeWorkloadObserver(WorkloadRuntimeStatus.PENDING)
    orchestrator, gpu_manager = create_orchestrator_with_observer(observer)
    job = prepare_observed_job(orchestrator)

    assert orchestrator.reconcile_workload(job.id) is True

    stored_job = orchestrator.job_manager.get_job(job.id)
    gpu = gpu_manager.get_gpu("gpu-001")

    assert stored_job.status == JobStatus.SCHEDULED
    assert gpu.status == GPUStatus.ALLOCATED
    assert gpu.free_vram_gb == 24


def test_reconcile_running_starts_job():
    from compute_fabric.execution.workload_observer import (
        WorkloadRuntimeStatus,
    )

    observer = FakeWorkloadObserver(WorkloadRuntimeStatus.RUNNING)
    orchestrator, _ = create_orchestrator_with_observer(observer)
    job = prepare_observed_job(orchestrator)

    assert orchestrator.reconcile_workload(job.id) is True

    stored_job = orchestrator.job_manager.get_job(job.id)

    assert stored_job.status == JobStatus.RUNNING


def test_reconcile_succeeded_completes_and_releases_gpu_once():
    from compute_fabric.execution.workload_observer import (
        WorkloadRuntimeStatus,
    )

    observer = FakeWorkloadObserver(WorkloadRuntimeStatus.SUCCEEDED)
    orchestrator, gpu_manager = create_orchestrator_with_observer(observer)
    job = prepare_observed_job(orchestrator)

    assert orchestrator.reconcile_workload(job.id) is True

    stored_job = orchestrator.job_manager.get_job(job.id)
    gpu = gpu_manager.get_gpu("gpu-001")

    assert stored_job.status == JobStatus.COMPLETED
    assert gpu.status == GPUStatus.AVAILABLE
    assert gpu.free_vram_gb == 64

    assert orchestrator.reconcile_workload(job.id) is True

    stored_job = orchestrator.job_manager.get_job(job.id)
    gpu = gpu_manager.get_gpu("gpu-001")

    assert stored_job.status == JobStatus.COMPLETED
    assert gpu.free_vram_gb == 64
    assert observer.calls == ["compute-fabric-job-observed-001"]


def test_reconcile_failed_fails_and_releases_gpu_once():
    from compute_fabric.execution.workload_observer import (
        WorkloadRuntimeStatus,
    )

    observer = FakeWorkloadObserver(WorkloadRuntimeStatus.FAILED)
    orchestrator, gpu_manager = create_orchestrator_with_observer(observer)
    job = prepare_observed_job(orchestrator)

    assert orchestrator.reconcile_workload(job.id) is True

    stored_job = orchestrator.job_manager.get_job(job.id)
    gpu = gpu_manager.get_gpu("gpu-001")

    assert stored_job.status == JobStatus.FAILED
    assert gpu.status == GPUStatus.AVAILABLE
    assert gpu.free_vram_gb == 64

    assert orchestrator.reconcile_workload(job.id) is True

    assert gpu.free_vram_gb == 64
    assert observer.calls == ["compute-fabric-job-observed-001"]
