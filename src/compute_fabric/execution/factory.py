from collections.abc import Mapping

from kubernetes import client, config

from compute_fabric.execution.kubernetes_workload_observer import (
    KubernetesWorkloadObserver,
)
from compute_fabric.execution.kubernetes_workload_runner import (
    KubernetesWorkloadRunner,
)
from compute_fabric.execution.kubernetes_workload_terminator import (
    KubernetesWorkloadTerminator,
)
from compute_fabric.execution.workload_observer import WorkloadObserver
from compute_fabric.execution.workload_runner import WorkloadRunner
from compute_fabric.execution.workload_terminator import WorkloadTerminator


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
        apps_api=client.AppsV1Api(),
        core_api=client.CoreV1Api(),
        namespace=namespace,
    )


def create_workload_observer(
    environment: Mapping[str, str],
) -> WorkloadObserver | None:
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

    return KubernetesWorkloadObserver(
        batch_api=client.BatchV1Api(),
        apps_api=client.AppsV1Api(),
        namespace=namespace,
    )

def create_workload_terminator(
    environment: Mapping[str, str],
) -> WorkloadTerminator | None:
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

    return KubernetesWorkloadTerminator(
        batch_api=client.BatchV1Api(),
        apps_api=client.AppsV1Api(),
        core_api=client.CoreV1Api(),
        namespace=namespace,
    )

