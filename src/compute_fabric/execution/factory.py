from collections.abc import Mapping

from kubernetes import client, config

from compute_fabric.execution.kubernetes_workload_runner import (
    KubernetesWorkloadRunner,
)
from compute_fabric.execution.workload_runner import WorkloadRunner


def create_workload_runner(
    environment: Mapping[str, str],
) -> WorkloadRunner | None:
    backend = environment.get(
        "COMPUTE_FABRIC_EXECUTION_BACKEND",
        "none",
    ).strip().lower()

    if backend in {"", "none"}:
        return None

    if backend != "kubernetes":
        raise RuntimeError(
            f"Unsupported execution backend: {backend}"
        )

    namespace = environment.get(
        "COMPUTE_FABRIC_WORKLOAD_NAMESPACE",
        "default",
    ).strip()

    if not namespace:
        raise RuntimeError(
            "COMPUTE_FABRIC_WORKLOAD_NAMESPACE must not be empty"
        )

    config.load_incluster_config()

    return KubernetesWorkloadRunner(
        batch_api=client.BatchV1Api(),
        namespace=namespace,
    )
