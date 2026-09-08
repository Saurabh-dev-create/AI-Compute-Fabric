import re

from kubernetes import client

from compute_fabric.execution.workload_runner import (
    WorkloadExecution,
)
from compute_fabric.execution.workload_spec import WorkloadSpec
from compute_fabric.jobs.job_manager import Job
from compute_fabric.scheduler.scheduler import SchedulingDecision


class KubernetesWorkloadRunner:
    def __init__(
        self,
        batch_api: client.BatchV1Api,
        apps_api: client.AppsV1Api | None = None,
        core_api: client.CoreV1Api | None = None,
        namespace: str = "default",
    ) -> None:
        self.batch_api = batch_api
        self.apps_api = apps_api
        self.core_api = core_api
        self.namespace = namespace

    def launch(
        self,
        job: Job,
        decision: SchedulingDecision,
        spec: WorkloadSpec,
    ) -> WorkloadExecution:
        if spec.execution_mode == "service":
            return self._launch_service(job, decision, spec)

        return self._launch_batch(job, decision, spec)

    def _launch_batch(
        self,
        job: Job,
        decision: SchedulingDecision,
        spec: WorkloadSpec,
    ) -> WorkloadExecution:
        workload_name = self._workload_name(job.id)

        container = self._container(spec)

        pod_spec = self._pod_spec(
            container=container,
            node_id=decision.node_id,
            restart_policy="Never",
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels=self._labels(job.id),
            ),
            spec=pod_spec,
        )

        kubernetes_job = client.V1Job(
            metadata=client.V1ObjectMeta(
                name=workload_name,
                labels=self._labels(job.id),
            ),
            spec=client.V1JobSpec(
                backoff_limit=0,
                template=template,
            ),
        )

        self.batch_api.create_namespaced_job(
            namespace=self.namespace,
            body=kubernetes_job,
        )

        return WorkloadExecution(
            job_id=job.id,
            workload_id=workload_name,
            node_id=decision.node_id,
        )

    def _launch_service(
        self,
        job: Job,
        decision: SchedulingDecision,
        spec: WorkloadSpec,
    ) -> WorkloadExecution:
        if self.apps_api is None or self.core_api is None:
            raise RuntimeError(
                "Kubernetes service workload APIs are not configured"
            )

        if spec.service_port is None:
            raise ValueError(
                "service_port is required for service workloads"
            )

        workload_name = self._workload_name(job.id)
        labels = self._labels(job.id)

        container = self._container(
            spec,
            service_port=spec.service_port,
        )

        pod_spec = self._pod_spec(
            container=container,
            node_id=decision.node_id,
            restart_policy="Always",
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=labels),
            spec=pod_spec,
        )

        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=workload_name,
                labels=labels,
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels=labels,
                ),
                template=template,
                progress_deadline_seconds=1800,
            ),
        )

        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=workload_name,
                labels=labels,
            ),
            spec=client.V1ServiceSpec(
                type="ClusterIP",
                selector=labels,
                ports=[
                    client.V1ServicePort(
                        name="http",
                        port=spec.service_port,
                        target_port=spec.service_port,
                        protocol="TCP",
                    )
                ],
            ),
        )

        self.apps_api.create_namespaced_deployment(
            namespace=self.namespace,
            body=deployment,
        )

        try:
            self.core_api.create_namespaced_service(
                namespace=self.namespace,
                body=service,
            )
        except Exception:
            self.apps_api.delete_namespaced_deployment(
                name=workload_name,
                namespace=self.namespace,
            )
            raise

        return WorkloadExecution(
            job_id=job.id,
            workload_id=workload_name,
            node_id=decision.node_id,
        )

    @staticmethod
    def _container(
        spec: WorkloadSpec,
        service_port: int | None = None,
    ) -> client.V1Container:
        ports = (
            [
                client.V1ContainerPort(
                    name="http",
                    container_port=service_port,
                    protocol="TCP",
                )
            ]
            if service_port is not None
            else None
        )

        readiness_probe = (
            client.V1Probe(
                tcp_socket=client.V1TCPSocketAction(
                    port=service_port,
                ),
                initial_delay_seconds=1,
                period_seconds=5,
                timeout_seconds=1,
                failure_threshold=6,
                success_threshold=1,
            )
            if service_port is not None
            else None
        )

        return client.V1Container(
            name="workload",
            image=spec.image,
            command=list(spec.command) or None,
            args=list(spec.args) or None,
            ports=ports,
            readiness_probe=readiness_probe,
            resources=client.V1ResourceRequirements(
                requests={
                    "nvidia.com/gpu": "1",
                },
                limits={
                    "nvidia.com/gpu": "1",
                },
            ),
        )

    @staticmethod
    def _pod_spec(
        container: client.V1Container,
        node_id: str,
        restart_policy: str,
    ) -> client.V1PodSpec:
        return client.V1PodSpec(
            restart_policy=restart_policy,
            node_name=node_id,
            tolerations=[
                client.V1Toleration(
                    key="dedicated",
                    operator="Equal",
                    value="gpu",
                    effect="NoSchedule",
                )
            ],
            containers=[container],
        )

    @staticmethod
    def _labels(job_id: str) -> dict[str, str]:
        return {
            "app": "compute-fabric-workload",
            "compute-fabric-job-id": job_id,
        }

    @staticmethod
    def _workload_name(job_id: str) -> str:
        normalized = re.sub(
            r"[^a-z0-9-]+",
            "-",
            job_id.lower(),
        )
        normalized = normalized.strip("-")

        if not normalized:
            normalized = "job"

        return f"compute-fabric-{normalized}"[:63].rstrip("-")
