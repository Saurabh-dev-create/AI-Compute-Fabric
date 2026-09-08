from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from compute_fabric.execution.kubernetes_workload_observer import (
    KubernetesWorkloadObserver,
)
from compute_fabric.execution.workload_observer import (
    WorkloadRuntimeStatus,
)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            SimpleNamespace(active=None, succeeded=None, failed=None),
            WorkloadRuntimeStatus.PENDING,
        ),
        (
            SimpleNamespace(active=1, succeeded=None, failed=None),
            WorkloadRuntimeStatus.RUNNING,
        ),
        (
            SimpleNamespace(active=0, succeeded=1, failed=0),
            WorkloadRuntimeStatus.SUCCEEDED,
        ),
        (
            SimpleNamespace(active=0, succeeded=0, failed=1),
            WorkloadRuntimeStatus.FAILED,
        ),
    ],
)
def test_observe_maps_kubernetes_job_status(
    status,
    expected,
) -> None:
    batch_api = Mock()
    batch_api.read_namespaced_job_status.return_value = (
        SimpleNamespace(status=status)
    )

    observer = KubernetesWorkloadObserver(
        batch_api=batch_api,
        namespace="ai-workloads",
    )

    observation = observer.observe("compute-fabric-test")

    assert observation.workload_id == "compute-fabric-test"
    assert observation.status == expected

    batch_api.read_namespaced_job_status.assert_called_once_with(
        name="compute-fabric-test",
        namespace="ai-workloads",
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            SimpleNamespace(
                ready_replicas=None,
                available_replicas=None,
                unavailable_replicas=1,
                conditions=[],
            ),
            WorkloadRuntimeStatus.PENDING,
        ),
        (
            SimpleNamespace(
                ready_replicas=1,
                available_replicas=1,
                unavailable_replicas=0,
                conditions=[],
            ),
            WorkloadRuntimeStatus.RUNNING,
        ),
        (
            SimpleNamespace(
                ready_replicas=0,
                available_replicas=0,
                unavailable_replicas=1,
                conditions=[
                    SimpleNamespace(
                        type="Progressing",
                        status="False",
                        reason="ProgressDeadlineExceeded",
                    )
                ],
            ),
            WorkloadRuntimeStatus.FAILED,
        ),
    ],
)
def test_observe_maps_kubernetes_deployment_status(
    status,
    expected,
) -> None:
    batch_api = Mock()
    apps_api = Mock()

    apps_api.read_namespaced_deployment_status.return_value = (
        SimpleNamespace(status=status)
    )

    observer = KubernetesWorkloadObserver(
        batch_api=batch_api,
        apps_api=apps_api,
        namespace="ai-workloads",
    )

    observation = observer.observe(
        "compute-fabric-vllm",
        "service",
    )

    assert observation.workload_id == "compute-fabric-vllm"
    assert observation.status == expected

    apps_api.read_namespaced_deployment_status.assert_called_once_with(
        name="compute-fabric-vllm",
        namespace="ai-workloads",
    )
    batch_api.read_namespaced_job_status.assert_not_called()
