"""In-memory backend data used by local tools and MCP server."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.config.settings import settings
from src.services.db import execute, query_one

ORDERS: dict[str, dict[str, Any]] = {
    "ORD-001": {
        "order_id": "ORD-001",
        "customer_name": "Priya Shah",
        "status": "Shipped",
        "eta": "2026-06-18",
        "carrier": "BlueDart",
        "can_cancel": False,
        "items": [{"product_id": "PHONE-RN13", "sku": "PRD-102", "name": "Redmi Note 13", "qty": 1}],
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "customer_name": "Maya Rao",
        "status": "Processing",
        "eta": "2026-06-20",
        "carrier": "DTDC",
        "can_cancel": True,
        "items": [{"product_id": "TV-SAM55", "sku": "PRD-201", "name": "Samsung Crystal 55 inch 4K TV", "qty": 1}],
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "customer_name": "Aarav Sharma",
        "status": "Delivered",
        "eta": "Delivered on 2026-06-10",
        "carrier": "FedEx",
        "can_cancel": False,
        "items": [{"product_id": "ACC-C65", "sku": "PRD-401", "name": "65 W USB-C Fast Charger", "qty": 2}],
    },
    "ORD-004": {
        "order_id": "ORD-004",
        "customer_name": "Leena Fernandes",
        "status": "Cancelled",
        "eta": "N/A",
        "carrier": "N/A",
        "can_cancel": False,
        "items": [{"product_id": "PHONE-A55", "sku": "PRD-101", "name": "Samsung Galaxy A55", "qty": 1}],
    },
}


def get_order_status_data(order_id: str) -> dict[str, Any]:
    clean = (order_id or "").strip().upper()
    if clean == "ORD-TIMEOUT":
        return {"ok": False, "error_type": "timeout", "message": "Order service timed out."}
    if settings.data_backend.lower() in {"postgres", "auto"}:
        try:
            order = query_one(
                "SELECT order_id, customer_name, status, eta, carrier, can_cancel FROM orders WHERE order_id=%s",
                (clean,),
            )
            return {"ok": True, **order, "items": []} if order else {"ok": False, "error_type": "not_found", "order_id": clean}
        except Exception:
            if settings.data_backend.lower() == "postgres":
                return {"ok": False, "error_type": "backend", "message": "PostgreSQL order service is unavailable."}
    order = ORDERS.get(clean)
    if not order:
        return {"ok": False, "error_type": "not_found", "order_id": clean}
    return {"ok": True, **deepcopy(order)}


def cancel_order_data(order_id: str, confirm: bool = True) -> dict[str, Any]:
    clean = (order_id or "").strip().upper()
    if settings.data_backend.lower() in {"postgres", "auto"}:
        try:
            order = query_one(
                "SELECT order_id, status, can_cancel FROM orders WHERE order_id=%s",
                (clean,),
            )
            if not order:
                return {"ok": False, "error_type": "not_found", "order_id": clean}
            if not confirm:
                return {"ok": False, "error_type": "confirmation_required", "message": "Cancellation requires confirmation."}
            if str(order["status"]).lower() == "cancelled":
                return {"ok": True, "order_id": clean, "message": f"Order {clean} is already cancelled."}
            if not order["can_cancel"]:
                return {"ok": False, "error_type": "not_allowed", "message": "This order cannot be cancelled because it has shipped, delivered, or already been cancelled."}
            execute("UPDATE orders SET status='Cancelled', can_cancel=false WHERE order_id=%s", (clean,))
            return {"ok": True, "order_id": clean, "message": f"Order {clean} has been cancelled."}
        except Exception:
            if settings.data_backend.lower() == "postgres":
                return {"ok": False, "error_type": "backend", "message": "PostgreSQL order service is unavailable."}

    order = ORDERS.get(clean)
    if not order:
        return {"ok": False, "error_type": "not_found", "order_id": clean}
    if not confirm:
        return {"ok": False, "error_type": "confirmation_required", "message": "Cancellation requires confirmation."}
    if not order["can_cancel"]:
        return {"ok": False, "error_type": "not_allowed", "message": "This order cannot be cancelled because it has shipped, delivered, or already been cancelled."}
    return {"ok": True, "order_id": clean, "message": f"Order {clean} has been cancelled."}


def get_invoice_data(order_id: str) -> dict[str, Any]:
    result = get_order_status_data(order_id)
    if not result.get("ok"):
        return result
    return {"ok": True, "order_id": result["order_id"], "invoice_url": f"https://ecombot.local/invoices/{result['order_id']}.pdf"}
