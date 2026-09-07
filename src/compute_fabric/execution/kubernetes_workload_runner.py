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
        namespace: str = "default",
    ) -> None:
        self.batch_api = batch_api
        self.namespace = namespace

    def launch(
        self,
        job: Job,
        decision: SchedulingDecision,
        spec: WorkloadSpec,
    ) -> WorkloadExecution:
        workload_name = self._workload_name(job.id)

        container = client.V1Container(
            name="workload",
            image=spec.image,
            command=list(spec.command) or None,
            args=list(spec.args) or None,
            resources=client.V1ResourceRequirements(
                requests={
                    "nvidia.com/gpu": "1",
                },
                limits={
                    "nvidia.com/gpu": "1",
                },
            ),
        )

        pod_spec = client.V1PodSpec(
            restart_policy="Never",
            node_name=decision.node_id,
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

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={
                    "app": "compute-fabric-workload",
                    "compute-fabric-job-id": job.id,
                },
            ),
            spec=pod_spec,
        )

        kubernetes_job = client.V1Job(
            metadata=client.V1ObjectMeta(
                name=workload_name,
                labels={
                    "app": "compute-fabric-workload",
                    "compute-fabric-job-id": job.id,
                },
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
