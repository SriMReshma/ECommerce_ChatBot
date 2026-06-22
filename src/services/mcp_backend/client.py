"""FastMCP client adapter supporting in-process and HTTP transports."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Any

from fastmcp import Client

from src.config.settings import settings


async def call_tool_async(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    from src.services.mcp_backend.server import build_server

    transport = settings.mcp_url if settings.mcp_transport.lower() == "http" else build_server()
    async with Client(transport) as client:
        result = await client.call_tool(name, arguments, _return_raw_result=True)
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured.get("result", structured)
    for item in getattr(result, "content", []):
        text = getattr(item, "text", "")
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"ok": True, "content": text}
    return {"ok": False, "error_type": "invalid_response", "message": "MCP returned no structured content."}


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(call_tool_async(name, arguments))
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(call_tool_async(name, arguments))).result(timeout=15)
