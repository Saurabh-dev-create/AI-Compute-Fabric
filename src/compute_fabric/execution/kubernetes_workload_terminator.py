from typing import Literal

from kubernetes import client


class KubernetesWorkloadTerminator:
    def __init__(
        self,
        batch_api: client.BatchV1Api,
        apps_api: client.AppsV1Api,
        core_api: client.CoreV1Api,
        namespace: str = "default",
    ) -> None:
        self.batch_api = batch_api
        self.apps_api = apps_api
        self.core_api = core_api
        self.namespace = namespace

    def terminate(
        self,
        workload_id: str,
        execution_mode: Literal["batch", "service"] = "batch",
    ) -> None:
        if execution_mode == "service":
            self._terminate_service(workload_id)
            return

        self.batch_api.delete_namespaced_job(
            name=workload_id,
            namespace=self.namespace,
            propagation_policy="Foreground",
        )

    def _terminate_service(
        self,
        workload_id: str,
    ) -> None:
        # Delete the Deployment first so no new serving pods can be created.
        self.apps_api.delete_namespaced_deployment(
            name=workload_id,
            namespace=self.namespace,
            propagation_policy="Foreground",
        )

        self.core_api.delete_namespaced_service(
            name=workload_id,
            namespace=self.namespace,
        )
