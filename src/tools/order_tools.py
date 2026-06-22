"""Order tools with validation and controlled errors."""

from __future__ import annotations

import re
from typing import Any

from src.services.order_store import cancel_order_data, get_invoice_data, get_order_status_data
from src.config.settings import settings


def _mcp(name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    if not settings.use_mcp:
        return None
    try:
        from src.services.mcp_backend.client import call_tool

        return call_tool(name, arguments)
    except Exception as exc:
        return {"ok": False, "error_type": "mcp", "message": f"MCP backend unavailable: {exc}"}

ORDER_RE = re.compile(r"^ORD-[0-9A-Z]{3,}$")


def validate_order_id(order_id: str) -> tuple[bool, str]:
    clean = (order_id or "").strip().upper()
    return bool(ORDER_RE.match(clean)), clean


def get_order_status(order_id: str) -> dict[str, Any]:
    valid, clean = validate_order_id(order_id)
    if not valid:
        return {"ok": False, "error_type": "validation", "message": "Use an order ID like ORD-001."}
    return _mcp("mcp_get_order_status", {"order_id": clean}) or get_order_status_data(clean)


def cancel_order(order_id: str) -> dict[str, Any]:
    valid, clean = validate_order_id(order_id)
    if not valid:
        return {"ok": False, "error_type": "validation", "message": "Use an order ID like ORD-002."}
    return _mcp("mcp_cancel_order", {"order_id": clean, "confirm": True}) or cancel_order_data(clean, confirm=True)


def get_invoice(order_id: str) -> dict[str, Any]:
    valid, clean = validate_order_id(order_id)
    if not valid:
        return {"ok": False, "error_type": "validation", "message": "Use an order ID like ORD-001."}
    return _mcp("mcp_get_invoice", {"order_id": clean}) or get_invoice_data(clean)
