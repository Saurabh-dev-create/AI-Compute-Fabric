from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from compute_fabric.common.enums import GPUStatus
from compute_fabric.gpu.gpu_inventory import GPU, GPUInventory
from compute_fabric.gpu.gpu_manager import GPUManager
from compute_fabric.jobs.job_manager import Job
from compute_fabric.jobs.job_state import JobStateManager
from compute_fabric.queue.admission import AdmissionController
from compute_fabric.queue.priority_queue import PriorityJobQueue
from compute_fabric.queue.queue_manager import QueueManager
from compute_fabric.queue.queue_processor import QueueProcessor
from compute_fabric.scheduler.resource_manager import ResourceManager
from compute_fabric.scheduler.scheduler import Scheduler
from compute_fabric.scheduler.scoring import GPUScorer
from compute_fabric.jobs.job_orchestrator import JobOrchestrator
from compute_fabric.jobs.job_manager import JobManager

app = FastAPI(
    title="AI Compute Fabric",
    description="AI-aware compute control plane for GPU workloads",
    version="0.1.0",
)


class JobRequest(BaseModel):
    job_id: str
    job_type: str
    gpu_type: str | None = None
    min_vram_gb: float
    priority: int


class JobResponse(BaseModel):
    job_id: str
    status: str
    gpu_id: str | None = None
    node_id: str | None = None
    score: float | None = None


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
job_manager = JobManager()

queue_processor = QueueProcessor(
    queue_manager,
    scheduler,
    state_manager,
)
orchestrator = JobOrchestrator(
    job_manager,
    queue_manager,
    queue_processor,
    scheduler,
    state_manager,
    gpu_manager,
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "AI Compute Fabric",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/gpus")
def list_gpus() -> list[GPU]:
    return gpu_manager.list_gpus()


@app.post("/jobs", response_model=JobResponse)
def submit_job(request: JobRequest) -> JobResponse:
    if job_manager.get_job(request.job_id) is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Job {request.job_id} already exists",
        )

    job = Job(
        id=request.job_id,
        job_type=request.job_type,
        gpu_type=request.gpu_type,
        min_vram_gb=request.min_vram_gb,
        priority=request.priority,
    )

    decision = orchestrator.submit_and_schedule(job)

    if decision is None:
        raise HTTPException(
            status_code=400,
            detail="Job could not be scheduled",
        )

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        gpu_id=job.gpu_id,
        node_id=job.node_id,
        score=decision.score,
    )


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found",
        )

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        gpu_id=job.gpu_id,
        node_id=job.node_id,
    )
