from types import SimpleNamespace

import pytest

from compute_fabric.mcp import devops_server
from compute_fabric.mcp.service import MCPService


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


@pytest.mark.anyio
async def test_service_discovers_tools_through_mcp() -> None:
    server = devops_server.create_devops_mcp_server()
    service = MCPService(server)

    tools = await service.list_tools()
    names = {tool["name"] for tool in tools}

    assert names == {
        "kubernetes_cluster_health",
        "kubernetes_workload_status",
        "gpu_cluster_status",
    }

    for tool in tools:
        assert tool["description"]
        assert tool["input_schema"]
        assert tool["output_schema"]


@pytest.mark.anyio
async def test_service_calls_gpu_tool_through_mcp(
    monkeypatch,
) -> None:
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
    service = MCPService(server)

    result = await service.call_tool(
        "gpu_cluster_status",
    )

    assert result == {
        "gpu_nodes": [
            {
                "name": "gpu-node",
                "allocatable_gpus": 1,
            }
        ],
        "gpu_node_count": 1,
        "allocatable_gpus": 1,
    }
