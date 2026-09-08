from unittest.mock import Mock

from compute_fabric.execution.kubernetes_workload_terminator import (
    KubernetesWorkloadTerminator,
)


def test_terminate_batch_deletes_kubernetes_job() -> None:
    batch_api = Mock()
    apps_api = Mock()
    core_api = Mock()

    terminator = KubernetesWorkloadTerminator(
        batch_api=batch_api,
        apps_api=apps_api,
        core_api=core_api,
        namespace="ai-workloads",
    )

    terminator.terminate(
        "compute-fabric-training",
        "batch",
    )

    batch_api.delete_namespaced_job.assert_called_once_with(
        name="compute-fabric-training",
        namespace="ai-workloads",
        propagation_policy="Foreground",
    )
    apps_api.delete_namespaced_deployment.assert_not_called()
    core_api.delete_namespaced_service.assert_not_called()


def test_terminate_service_deletes_deployment_then_service() -> None:
    calls = []

    apps_api = Mock()
    core_api = Mock()
    batch_api = Mock()

    apps_api.delete_namespaced_deployment.side_effect = (
        lambda **kwargs: calls.append(("deployment", kwargs))
    )
    core_api.delete_namespaced_service.side_effect = (
        lambda **kwargs: calls.append(("service", kwargs))
    )

    terminator = KubernetesWorkloadTerminator(
        batch_api=batch_api,
        apps_api=apps_api,
        core_api=core_api,
        namespace="ai-workloads",
    )

    terminator.terminate(
        "compute-fabric-vllm",
        "service",
    )

    assert [kind for kind, _ in calls] == [
        "deployment",
        "service",
    ]

    apps_api.delete_namespaced_deployment.assert_called_once_with(
        name="compute-fabric-vllm",
        namespace="ai-workloads",
        propagation_policy="Foreground",
    )
    core_api.delete_namespaced_service.assert_called_once_with(
        name="compute-fabric-vllm",
        namespace="ai-workloads",
    )
    batch_api.delete_namespaced_job.assert_not_called()
