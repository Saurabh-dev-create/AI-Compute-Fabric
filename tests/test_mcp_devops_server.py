from types import SimpleNamespace

import pytest

from compute_fabric.mcp import devops_server


def _node(name: str, ready: bool, gpus: str = "0"):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name),
        status=SimpleNamespace(
            conditions=[
                SimpleNamespace(
                    type="Ready",
                    status="True" if ready else "False",
                )
            ],
            allocatable={"nvidia.com/gpu": gpus},
        ),
    )


def _pod(phase: str):
    return SimpleNamespace(
        status=SimpleNamespace(phase=phase),
    )


@pytest.mark.anyio
async def test_mcp_lists_devops_tools() -> None:
    server = devops_server.create_devops_mcp_server()

    tools = await server.list_tools()
    names = {tool.name for tool in tools}

    assert names == {
        "kubernetes_cluster_health",
        "kubernetes_workload_status",
        "gpu_cluster_status",
    }


@pytest.mark.anyio
async def test_cluster_health_tool_through_mcp(monkeypatch) -> None:
    monkeypatch.setattr(
        devops_server,
        "_load_kubernetes_configuration",
        lambda: None,
    )

    class FakeCoreV1Api:
        def list_node(self):
            return SimpleNamespace(
                items=[
                    _node("cpu-node", True),
                    _node("unready-node", False),
                ]
            )

        def list_pod_for_all_namespaces(self):
            return SimpleNamespace(
                items=[
                    _pod("Running"),
                    _pod("Running"),
                    _pod("Pending"),
                ]
            )

    monkeypatch.setattr(
        devops_server.client,
        "CoreV1Api",
        FakeCoreV1Api,
    )

    server = devops_server.create_devops_mcp_server()

    result = await server.call_tool(
        "kubernetes_cluster_health",
        {},
    )

    assert result.structured_content == {
        "nodes": {
            "total": 2,
            "ready": 1,
            "not_ready": 1,
        },
        "pods": {
            "Pending": 1,
            "Running": 2,
        },
    }


@pytest.mark.anyio
async def test_gpu_cluster_status_tool_through_mcp(monkeypatch) -> None:
    monkeypatch.setattr(
        devops_server,
        "_load_kubernetes_configuration",
        lambda: None,
    )

    class FakeCoreV1Api:
        def list_node(self):
            return SimpleNamespace(
                items=[
                    _node("cpu-node", True),
                    _node("gpu-node", True, "1"),
                ]
            )

    monkeypatch.setattr(
        devops_server.client,
        "CoreV1Api",
        FakeCoreV1Api,
    )

    server = devops_server.create_devops_mcp_server()

    result = await server.call_tool(
        "gpu_cluster_status",
        {},
    )

    assert result.structured_content == {
        "gpu_nodes": [
            {
                "name": "gpu-node",
                "allocatable_gpus": 1,
            }
        ],
        "gpu_node_count": 1,
        "allocatable_gpus": 1,
    }


@pytest.mark.anyio
async def test_workload_status_tool_through_mcp(monkeypatch) -> None:
    monkeypatch.setattr(
        devops_server,
        "_load_kubernetes_configuration",
        lambda: None,
    )

    class FakeAppsV1Api:
        def read_namespaced_deployment(self, name, namespace):
            assert name == "inference"
            assert namespace == "default"

            return SimpleNamespace(
                spec=SimpleNamespace(replicas=1),
                status=SimpleNamespace(
                    ready_replicas=1,
                    available_replicas=1,
                ),
            )

    monkeypatch.setattr(
        devops_server.client,
        "AppsV1Api",
        FakeAppsV1Api,
    )

    server = devops_server.create_devops_mcp_server()

    result = await server.call_tool(
        "kubernetes_workload_status",
        {
            "namespace": "default",
            "name": "inference",
            "kind": "deployment",
        },
    )

    assert result.structured_content == {
        "kind": "Deployment",
        "namespace": "default",
        "name": "inference",
        "desired_replicas": 1,
        "ready_replicas": 1,
        "available_replicas": 1,
        "active": None,
        "succeeded": None,
        "failed": None,
    }
