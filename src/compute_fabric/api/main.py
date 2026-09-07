import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from compute_fabric.common.enums import GPUStatus
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
from compute_fabric.storage.postgres_repository import PostgresJobRepository
from compute_fabric.telemetry.gpu_metrics import update_gpu_metrics
from compute_fabric.telemetry.metrics import (
    JOB_ADMISSION_REJECTIONS,
    JOB_LIFECYCLE_TRANSITIONS,
    JOB_SUBMISSIONS,
    SCHEDULING_ATTEMPTS,
    SCHEDULING_LATENCY_SECONDS,
    SCHEDULING_RESULTS,
)
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from psycopg import connect
from psycopg.errors import OperationalError


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not configured")


app = FastAPI(
    title="AI Compute Fabric",
    description="AI-aware compute control plane for GPU workloads",
    version="0.1.0",
)


class JobRequest(BaseModel):
    job_id: str
    job_type: str
    gpu_type: str | None = None
    min_vram_gb: float = Field(gt=0)
    priority: int = Field(ge=0)


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

repository = PostgresJobRepository(DATABASE_URL)
job_manager = JobManager(repository)

queue_processor = QueueProcessor(
    queue_manager,
    scheduler,
    state_manager,
)

orchestrator = JobOrchestrator(
    job_manager=job_manager,
    queue_manager=queue_manager,
    queue_processor=queue_processor,
    scheduler=scheduler,
    state_manager=state_manager,
    gpu_manager=gpu_manager,
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "AI Compute Fabric",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/ready")
def ready(response: Response) -> dict[str, str]:
    try:
        with connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
    except OperationalError:
        response.status_code = 503
        return {"status": "not_ready"}

    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    update_gpu_metrics(inventory)

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


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

    JOB_SUBMISSIONS.inc()

    if not admission_controller.admit(job):
        JOB_ADMISSION_REJECTIONS.inc()
        raise HTTPException(
            status_code=400,
            detail="Job rejected by admission controller",
        )

    SCHEDULING_ATTEMPTS.inc()

    with SCHEDULING_LATENCY_SECONDS.time():
        decision = orchestrator.submit_and_schedule(job)

    if decision is None:
        SCHEDULING_RESULTS.labels(result="pending").inc()
        stored_job = job_manager.get_job(job.id)

        if stored_job is None:
            raise HTTPException(
                status_code=500,
                detail="Job submission failed unexpectedly",
            )

        return JobResponse(
            job_id=stored_job.id,
            status=stored_job.status.value,
            gpu_id=stored_job.gpu_id,
            node_id=stored_job.node_id,
        )

    SCHEDULING_RESULTS.labels(result="scheduled").inc()
    JOB_LIFECYCLE_TRANSITIONS.labels(status=job.status.value).inc()

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        gpu_id=job.gpu_id,
        node_id=job.node_id,
        score=decision.score,
    )


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs() -> list[JobResponse]:
    return [
        JobResponse(
            job_id=job.id,
            status=job.status.value,
            gpu_id=job.gpu_id,
            node_id=job.node_id,
        )
        for job in job_manager.list_jobs()
    ]


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


@app.post("/jobs/{job_id}/start", response_model=JobResponse)
def start_job(job_id: str) -> JobResponse:
    if not orchestrator.start_job(job_id):
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found",
        )

    job = job_manager.get_job(job_id)
    JOB_LIFECYCLE_TRANSITIONS.labels(status=job.status.value).inc()

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        gpu_id=job.gpu_id,
        node_id=job.node_id,
    )


@app.post("/jobs/{job_id}/complete", response_model=JobResponse)
def complete_job(job_id: str) -> JobResponse:
    if not orchestrator.complete_job(job_id):
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found or GPU release failed",
        )

    job = job_manager.get_job(job_id)
    JOB_LIFECYCLE_TRANSITIONS.labels(status=job.status.value).inc()

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        gpu_id=job.gpu_id,
        node_id=job.node_id,
    )


@app.post("/jobs/{job_id}/fail", response_model=JobResponse)
def fail_job(job_id: str) -> JobResponse:
    if not orchestrator.fail_job(job_id):
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found or GPU release failed",
        )

    job = job_manager.get_job(job_id)
    JOB_LIFECYCLE_TRANSITIONS.labels(status=job.status.value).inc()

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        gpu_id=job.gpu_id,
        node_id=job.node_id,
    )


@app.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str) -> JobResponse:
    if not orchestrator.cancel_job(job_id):
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found or GPU release failed",
        )

    job = job_manager.get_job(job_id)
    JOB_LIFECYCLE_TRANSITIONS.labels(status=job.status.value).inc()

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        gpu_id=job.gpu_id,
        node_id=job.node_id,
    )
