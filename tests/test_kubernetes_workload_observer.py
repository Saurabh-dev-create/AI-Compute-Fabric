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
