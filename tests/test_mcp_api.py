from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from compute_fabric.api import main


def test_list_mcp_tools(monkeypatch) -> None:
    tools = [
        {
            "name": "gpu_cluster_status",
            "description": "Return GPU node and allocatable GPU summary.",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
        }
    ]

    list_tools = AsyncMock(return_value=tools)
    monkeypatch.setattr(main.mcp_service, "list_tools", list_tools)

    with TestClient(main.app) as client:
        response = client.get("/mcp/tools")

    assert response.status_code == 200
    assert response.json() == tools
    list_tools.assert_awaited_once_with()


def test_call_mcp_tool(monkeypatch) -> None:
    result = {
        "gpu_nodes": [],
        "gpu_node_count": 0,
        "allocatable_gpus": 0,
    }

    call_tool = AsyncMock(return_value=result)
    monkeypatch.setattr(main.mcp_service, "call_tool", call_tool)

    with TestClient(main.app) as client:
        response = client.post(
            "/mcp/call",
            json={
                "name": "gpu_cluster_status",
                "arguments": {},
            },
        )

    assert response.status_code == 200
    assert response.json() == result
    call_tool.assert_awaited_once_with(
        "gpu_cluster_status",
        {},
    )


def test_call_mcp_tool_failure(monkeypatch) -> None:
    call_tool = AsyncMock(
        side_effect=RuntimeError("MCP tool failed")
    )
    monkeypatch.setattr(main.mcp_service, "call_tool", call_tool)

    with TestClient(main.app) as client:
        response = client.post(
            "/mcp/call",
            json={
                "name": "gpu_cluster_status",
                "arguments": {},
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "MCP tool failed",
    }
