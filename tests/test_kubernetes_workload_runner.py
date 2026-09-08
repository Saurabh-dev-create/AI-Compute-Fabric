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
        service_account_name="compute-fabric-workload",
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
    assert (
        pod_spec.service_account_name
        == "compute-fabric-workload"
    )

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


class FakeAppsAPI:
    def __init__(self) -> None:
        self.namespace: str | None = None
        self.body: Any = None
        self.deleted_name: str | None = None
        self.deleted_namespace: str | None = None

    def create_namespaced_deployment(
        self,
        namespace: str,
        body: Any,
    ) -> None:
        self.namespace = namespace
        self.body = body

    def delete_namespaced_deployment(
        self,
        name: str,
        namespace: str,
    ) -> None:
        self.deleted_name = name
        self.deleted_namespace = namespace


class FakeCoreAPI:
    def __init__(self) -> None:
        self.namespace: str | None = None
        self.body: Any = None
        self.fail_create = False

    def create_namespaced_service(
        self,
        namespace: str,
        body: Any,
    ) -> None:
        if self.fail_create:
            raise RuntimeError("service creation failed")

        self.namespace = namespace
        self.body = body


def test_kubernetes_runner_builds_gpu_service_on_selected_node() -> None:
    batch_api = FakeBatchAPI()
    apps_api = FakeAppsAPI()
    core_api = FakeCoreAPI()

    runner = KubernetesWorkloadRunner(
        batch_api=batch_api,
        apps_api=apps_api,
        core_api=core_api,
        namespace="ai-workloads",
    )

    job = Job(
        id="vllm-service-001",
        job_type="inference",
        gpu_type="T4",
        min_vram_gb=4.0,
        priority=10,
    )

    decision = SchedulingDecision(
        job_id=job.id,
        gpu_id="GPU-real-001",
        node_id="gpu-node-01",
        score=1.5,
    )

    spec = WorkloadSpec(
        image="example/vllm:latest",
        args=("--model", "example/model"),
        execution_mode="service",
        service_port=8000,
    )

    execution = runner.launch(job, decision, spec)

    assert batch_api.body is None

    deployment = apps_api.body
    assert deployment.metadata.name == "compute-fabric-vllm-service-001"
    assert deployment.spec.replicas == 1
    assert deployment.spec.progress_deadline_seconds == 1800

    pod_spec = deployment.spec.template.spec
    assert pod_spec.node_name == decision.node_id
    assert pod_spec.restart_policy == "Always"

    container = pod_spec.containers[0]
    assert container.image == spec.image
    assert container.args == ["--model", "example/model"]
    assert container.ports[0].container_port == 8000

    assert container.readiness_probe is not None
    assert container.readiness_probe.tcp_socket.port == 8000
    assert container.readiness_probe.initial_delay_seconds == 1
    assert container.readiness_probe.period_seconds == 5
    assert container.readiness_probe.timeout_seconds == 1
    assert container.readiness_probe.failure_threshold == 6
    assert container.readiness_probe.success_threshold == 1

    assert container.resources.requests == {
        "nvidia.com/gpu": "1",
    }
    assert container.resources.limits == {
        "nvidia.com/gpu": "1",
    }

    service = core_api.body
    assert service.metadata.name == "compute-fabric-vllm-service-001"
    assert service.spec.type == "ClusterIP"
    assert service.spec.ports[0].port == 8000
    assert service.spec.ports[0].target_port == 8000
    assert service.spec.selector == deployment.spec.selector.match_labels

    assert execution.job_id == job.id
    assert execution.workload_id == "compute-fabric-vllm-service-001"
    assert execution.node_id == decision.node_id


def test_kubernetes_service_creation_failure_cleans_up_deployment() -> None:
    batch_api = FakeBatchAPI()
    apps_api = FakeAppsAPI()
    core_api = FakeCoreAPI()
    core_api.fail_create = True

    runner = KubernetesWorkloadRunner(
        batch_api=batch_api,
        apps_api=apps_api,
        core_api=core_api,
    )

    job = Job(
        id="service-cleanup-001",
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

    spec = WorkloadSpec(
        image="example/vllm:latest",
        execution_mode="service",
        service_port=8000,
    )

    try:
        runner.launch(job, decision, spec)
    except RuntimeError as exc:
        assert str(exc) == "service creation failed"
    else:
        raise AssertionError("Expected service creation failure")

    assert (
        apps_api.deleted_name
        == "compute-fabric-service-cleanup-001"
    )
    assert apps_api.deleted_namespace == "default"
