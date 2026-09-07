from typing import Any

from compute_fabric.execution.kubernetes_workload_runner import (
    KubernetesWorkloadRunner,
)
from compute_fabric.execution.workload_spec import WorkloadSpec
from compute_fabric.jobs.job_manager import Job
from compute_fabric.scheduler.scheduler import SchedulingDecision


class FakeBatchAPI:
    def __init__(self) -> None:
        self.namespace: str | None = None
        self.body: Any = None

    def create_namespaced_job(
        self,
        namespace: str,
        body: Any,
    ) -> None:
        self.namespace = namespace
        self.body = body


def test_kubernetes_runner_builds_gpu_job_on_selected_node() -> None:
    batch_api = FakeBatchAPI()

    runner = KubernetesWorkloadRunner(
        batch_api=batch_api,
        namespace="default",
    )

    job = Job(
        id="real-gpu-001",
        job_type="inference",
        gpu_type="T4",
        min_vram_gb=4.0,
        priority=10,
    )

    decision = SchedulingDecision(
        job_id=job.id,
        gpu_id="GPU-real-001",
        node_id="ip-10-20-59-87.ap-south-1.compute.internal",
        score=1.5,
    )

    spec = WorkloadSpec(
        image="nvidia/cuda:12.8.1-base-ubuntu24.04",
        command=("sh", "-c"),
        args=("nvidia-smi",),
    )

    execution = runner.launch(
        job,
        decision,
        spec,
    )

    assert batch_api.namespace == "default"

    kubernetes_job = batch_api.body

    assert kubernetes_job.metadata.name == "compute-fabric-real-gpu-001"

    pod_spec = kubernetes_job.spec.template.spec

    assert pod_spec.node_name == decision.node_id
    assert pod_spec.restart_policy == "Never"

    container = pod_spec.containers[0]

    assert container.image == spec.image
    assert container.command == ["sh", "-c"]
    assert container.args == ["nvidia-smi"]

    assert container.resources.requests == {
        "nvidia.com/gpu": "1",
    }
    assert container.resources.limits == {
        "nvidia.com/gpu": "1",
    }

    toleration = pod_spec.tolerations[0]

    assert toleration.key == "dedicated"
    assert toleration.value == "gpu"
    assert toleration.effect == "NoSchedule"

    assert execution.job_id == job.id
    assert execution.workload_id == "compute-fabric-real-gpu-001"
    assert execution.node_id == decision.node_id


def test_kubernetes_runner_normalizes_workload_name() -> None:
    batch_api = FakeBatchAPI()
    runner = KubernetesWorkloadRunner(batch_api=batch_api)

    job = Job(
        id="Inference_JOB_001",
        job_type="inference",
        gpu_type="T4",
        min_vram_gb=4.0,
        priority=1,
    )

    decision = SchedulingDecision(
        job_id=job.id,
        gpu_id="gpu-001",
        node_id="gpu-node-01",
        score=1.0,
    )

    runner.launch(
        job,
        decision,
        WorkloadSpec(image="example/image:latest"),
    )

    assert (
        batch_api.body.metadata.name
        == "compute-fabric-inference-job-001"
    )
