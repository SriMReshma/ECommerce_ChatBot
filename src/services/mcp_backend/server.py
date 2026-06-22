"""FastMCP-compatible order and inventory backend."""

from __future__ import annotations

from src.config.settings import settings
from src.rag.retriever import find_product
from src.services.order_store import cancel_order_data, get_invoice_data, get_order_status_data


def _check_stock(product_id_or_sku: str) -> dict:
    product = find_product(product_id_or_sku)
    if not product:
        return {"ok": False, "error_type": "not_found", "query": product_id_or_sku}
    return {
        "ok": True,
        "product_id": product["id"],
        "sku": product["sku"],
        "name": product["name"],
        "stock": product["stock"],
        "available": product["stock"] > 0,
    }


def _list_variants(product_id_or_name: str) -> dict:
    product = find_product(product_id_or_name)
    if not product:
        return {"ok": False, "error_type": "not_found", "query": product_id_or_name}
    return {"ok": True, "product_id": product["id"], "name": product["name"], "variants": product["variants"], "colors": product["colors"]}


def build_server():
    try:
        from fastmcp import FastMCP
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError as exc:
            raise RuntimeError("Install fastmcp or mcp to run the MCP backend.") from exc

    server = FastMCP("ecombot-backend")

    @server.tool()
    def mcp_get_order_status(order_id: str) -> dict:
        return get_order_status_data(order_id)

    @server.tool()
    def mcp_cancel_order(order_id: str, confirm: bool = True) -> dict:
        return cancel_order_data(order_id, confirm=confirm)

    @server.tool()
    def mcp_get_invoice(order_id: str) -> dict:
        return get_invoice_data(order_id)

    @server.tool()
    def mcp_check_stock(product_id_or_sku: str) -> dict:
        return _check_stock(product_id_or_sku)

    @server.tool()
    def mcp_list_variants(product_id_or_name: str) -> dict:
        return _list_variants(product_id_or_name)

    return server


if __name__ == "__main__":
    transport = "streamable-http"
    server = build_server()
    try:
        server.run(transport=transport, host=settings.mcp_host, port=settings.mcp_port)
    except TypeError:
        server.run(transport=transport)
