from typing import Literal

from kubernetes import client

from compute_fabric.execution.workload_observer import (
    WorkloadObservation,
    WorkloadRuntimeStatus,
)


class KubernetesWorkloadObserver:
    def __init__(
        self,
        batch_api: client.BatchV1Api,
        apps_api: client.AppsV1Api | None = None,
        namespace: str = "default",
    ) -> None:
        self.batch_api = batch_api
        self.apps_api = apps_api
        self.namespace = namespace

    def observe(
        self,
        workload_id: str,
        execution_mode: Literal["batch", "service"] = "batch",
    ) -> WorkloadObservation:
        if execution_mode == "service":
            return self._observe_service(workload_id)

        return self._observe_batch(workload_id)

    def _observe_batch(
        self,
        workload_id: str,
    ) -> WorkloadObservation:
        kubernetes_job = self.batch_api.read_namespaced_job_status(
            name=workload_id,
            namespace=self.namespace,
        )

        status = kubernetes_job.status

        if status.failed and status.failed > 0:
            runtime_status = WorkloadRuntimeStatus.FAILED
        elif status.succeeded and status.succeeded > 0:
            runtime_status = WorkloadRuntimeStatus.SUCCEEDED
        elif status.active and status.active > 0:
            runtime_status = WorkloadRuntimeStatus.RUNNING
        else:
            runtime_status = WorkloadRuntimeStatus.PENDING

        return WorkloadObservation(
            workload_id=workload_id,
            status=runtime_status,
        )

    def _observe_service(
        self,
        workload_id: str,
    ) -> WorkloadObservation:
        if self.apps_api is None:
            raise RuntimeError(
                "Kubernetes service workload API is not configured"
            )

        deployment = self.apps_api.read_namespaced_deployment_status(
            name=workload_id,
            namespace=self.namespace,
        )

        status = deployment.status

        unavailable = status.unavailable_replicas or 0
        ready = status.ready_replicas or 0
        available = status.available_replicas or 0

        conditions = status.conditions or []

        failed = any(
            condition.type == "Progressing"
            and condition.status == "False"
            and condition.reason == "ProgressDeadlineExceeded"
            for condition in conditions
        )

        if failed:
            runtime_status = WorkloadRuntimeStatus.FAILED
        elif ready > 0 and available > 0:
            runtime_status = WorkloadRuntimeStatus.RUNNING
        elif unavailable > 0:
            runtime_status = WorkloadRuntimeStatus.PENDING
        else:
            runtime_status = WorkloadRuntimeStatus.PENDING

        return WorkloadObservation(
            workload_id=workload_id,
            status=runtime_status,
        )
