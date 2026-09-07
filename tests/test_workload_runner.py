from compute_fabric.execution.workload_spec import WorkloadSpec
from compute_fabric.execution.workload_runner import (
    WorkloadExecution,
    WorkloadRunner,
)
from compute_fabric.jobs.job_manager import Job
from compute_fabric.scheduler.scheduler import SchedulingDecision


class FakeWorkloadRunner:
    def launch(
        self,
        job: Job,
        decision: SchedulingDecision,
        spec: WorkloadSpec,
    ) -> WorkloadExecution:
        return WorkloadExecution(
            job_id=job.id,
            workload_id=f"workload-{job.id}",
            node_id=decision.node_id,
        )


def test_workload_runner_contract() -> None:
    runner: WorkloadRunner = FakeWorkloadRunner()

    job = Job(
        id="job-001",
        job_type="inference",
        gpu_type="T4",
        min_vram_gb=4.0,
        priority=10,
    )

    decision = SchedulingDecision(
        job_id=job.id,
        gpu_id="gpu-001",
        node_id="gpu-node-01",
        score=1.25,
    )

    spec = WorkloadSpec(
        image="nvidia/cuda:12.8.1-base-ubuntu24.04",
    )

    execution = runner.launch(job, decision, spec)

    assert execution.job_id == "job-001"
    assert execution.workload_id == "workload-job-001"
    assert execution.node_id == "gpu-node-01"
