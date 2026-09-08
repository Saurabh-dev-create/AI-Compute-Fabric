from __future__ import annotations

from collections import Counter

from kubernetes import client, config
from mcp.server import MCPServer
from pydantic import BaseModel


class NodeHealth(BaseModel):
    total: int
    ready: int
    not_ready: int


class ClusterHealthResult(BaseModel):
    nodes: NodeHealth
    pods: dict[str, int]


class WorkloadStatusResult(BaseModel):
    kind: str
    namespace: str
    name: str
    desired_replicas: int | None = None
    ready_replicas: int | None = None
    available_replicas: int | None = None
    active: int | None = None
    succeeded: int | None = None
    failed: int | None = None


class GPUNodeStatus(BaseModel):
    name: str
    allocatable_gpus: int


class GPUClusterStatusResult(BaseModel):
    gpu_nodes: list[GPUNodeStatus]
    gpu_node_count: int
    allocatable_gpus: int



def _load_kubernetes_configuration() -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def create_devops_mcp_server() -> MCPServer:
    server = MCPServer("ai-compute-fabric-devops")

    @server.tool(structured_output=True)
    def kubernetes_cluster_health() -> ClusterHealthResult:
        """Return Kubernetes node and pod health summary."""
        _load_kubernetes_configuration()

        core = client.CoreV1Api()

        nodes = core.list_node().items
        pods = core.list_pod_for_all_namespaces().items

        ready_nodes = 0
        for node in nodes:
            for condition in node.status.conditions or []:
                if (
                    condition.type == "Ready"
                    and condition.status == "True"
                ):
                    ready_nodes += 1
                    break

        pod_phases = Counter(
            pod.status.phase or "Unknown"
            for pod in pods
        )

        return ClusterHealthResult(
            nodes=NodeHealth(
                total=len(nodes),
                ready=ready_nodes,
                not_ready=len(nodes) - ready_nodes,
            ),
            pods=dict(sorted(pod_phases.items())),
        )

    @server.tool(structured_output=True)
    def kubernetes_workload_status(
        namespace: str,
        name: str,
        kind: str = "deployment",
    ) -> WorkloadStatusResult:
        """Return status for a Kubernetes Deployment or Job."""
        _load_kubernetes_configuration()

        normalized_kind = kind.lower()

        if normalized_kind == "deployment":
            apps = client.AppsV1Api()
            workload = apps.read_namespaced_deployment(
                name=name,
                namespace=namespace,
            )

            return WorkloadStatusResult(
                kind="Deployment",
                namespace=namespace,
                name=name,
                desired_replicas=workload.spec.replicas,
                ready_replicas=workload.status.ready_replicas or 0,
                available_replicas=(
                    workload.status.available_replicas or 0
                ),
            )

        if normalized_kind == "job":
            batch = client.BatchV1Api()
            workload = batch.read_namespaced_job(
                name=name,
                namespace=namespace,
            )

            return WorkloadStatusResult(
                kind="Job",
                namespace=namespace,
                name=name,
                active=workload.status.active or 0,
                succeeded=workload.status.succeeded or 0,
                failed=workload.status.failed or 0,
            )

        raise ValueError(
            "Unsupported workload kind. Expected deployment or job."
        )

    @server.tool(structured_output=True)
    def gpu_cluster_status() -> GPUClusterStatusResult:
        """Return GPU node and allocatable GPU summary."""
        _load_kubernetes_configuration()

        core = client.CoreV1Api()
        nodes = core.list_node().items

        gpu_nodes = []
        total_allocatable_gpus = 0

        for node in nodes:
            allocatable = node.status.allocatable or {}
            gpu_count = int(
                allocatable.get("nvidia.com/gpu", "0")
            )

            if gpu_count <= 0:
                continue

            total_allocatable_gpus += gpu_count

            gpu_nodes.append(
                {
                    "name": node.metadata.name,
                    "allocatable_gpus": gpu_count,
                }
            )

        return GPUClusterStatusResult(
            gpu_nodes=[
                GPUNodeStatus(**gpu_node)
                for gpu_node in gpu_nodes
            ],
            gpu_node_count=len(gpu_nodes),
            allocatable_gpus=total_allocatable_gpus,
        )

    return server
