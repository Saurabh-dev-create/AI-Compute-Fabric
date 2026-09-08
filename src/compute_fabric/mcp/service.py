from __future__ import annotations

from typing import Any

from mcp import Client
from mcp.server import MCPServer


class MCPService:
    """Consume an MCP server through the official MCP client."""

    def __init__(self, server: MCPServer) -> None:
        self._server = server

    async def list_tools(self) -> list[dict[str, Any]]:
        async with Client(self._server) as client:
            result = await client.list_tools()

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
            }
            for tool in result.tools
        ]

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with Client(self._server) as client:
            result = await client.call_tool(
                name,
                arguments or {},
            )

        if result.is_error:
            messages = [
                block.text
                for block in result.content
                if getattr(block, "type", None) == "text"
            ]
            raise RuntimeError(
                "; ".join(messages)
                or f"MCP tool {name!r} failed"
            )

        if result.structured_content is not None:
            return result.structured_content

        raise RuntimeError(
            f"MCP tool {name!r} returned no structured content"
        )
