from kubernetes import client

from compute_fabric.execution.workload_observer import (
    WorkloadObservation,
    WorkloadRuntimeStatus,
)


class KubernetesWorkloadObserver:
    def __init__(
        self,
        batch_api: client.BatchV1Api,
        namespace: str = "default",
    ) -> None:
        self.batch_api = batch_api
        self.namespace = namespace

    def observe(
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
