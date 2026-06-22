"""Product and inventory tools."""

from __future__ import annotations

from typing import Any

from src.config.settings import settings
from src.rag.retriever import find_product, load_products, products_under_budget
from src.services.db import query_all, query_one


def _database_product(value: str) -> dict[str, Any] | None:
    if settings.data_backend.lower() not in {"postgres", "auto"}:
        return None
    clean = (value or "").strip()
    try:
        row = query_one(
            "SELECT product_id AS id, sku, name, category, price_inr, stock, active "
            "FROM products WHERE active=true AND (lower(product_id)=lower(%s) OR lower(sku)=lower(%s) OR lower(name)=lower(%s))",
            (clean, clean, clean),
        )
    except Exception:
        if settings.data_backend.lower() == "postgres":
            raise
        return None
    if not row:
        return None
    catalog = find_product(row["id"]) or {}
    return {**catalog, **row}


def lookup_product(value: str) -> dict[str, Any]:
    try:
        product = _database_product(value) or find_product(value)
    except Exception:
        return {"ok": False, "error_type": "backend", "message": "PostgreSQL product service is unavailable."}
    if not product:
        return {"ok": False, "error_type": "not_found", "query": value}
    return {"ok": True, **product}


def check_stock(value: str) -> dict[str, Any]:
    if settings.use_mcp:
        try:
            from src.services.mcp_backend.client import call_tool

            return call_tool("mcp_check_stock", {"product_id_or_sku": value})
        except Exception as exc:
            return {"ok": False, "error_type": "mcp", "message": f"MCP backend unavailable: {exc}"}
    try:
        product = _database_product(value) or find_product(value)
    except Exception:
        return {"ok": False, "error_type": "backend", "message": "PostgreSQL inventory service is unavailable."}
    if not product:
        return {"ok": False, "error_type": "not_found", "query": value}
    return {"ok": True, "product_id": product["id"], "sku": product["sku"], "name": product["name"], "stock": product["stock"], "available": product["stock"] > 0}


def list_variants(value: str) -> dict[str, Any]:
    if settings.use_mcp:
        try:
            from src.services.mcp_backend.client import call_tool

            return call_tool("mcp_list_variants", {"product_id_or_name": value})
        except Exception as exc:
            return {"ok": False, "error_type": "mcp", "message": f"MCP backend unavailable: {exc}"}
    product = find_product(value)
    if product:
        return {"ok": True, "product_id": product["id"], "name": product["name"], "variants": product["variants"], "colors": product["colors"]}
    lowered = (value or "").lower()
    matches = [product for product in load_products() if lowered in product["category"].lower() or lowered in product["name"].lower()]
    if not matches:
        return {"ok": False, "error_type": "not_found", "query": value}
    return {"ok": True, "variants": [{"product_id": p["id"], "name": p["name"], "variants": p["variants"], "colors": p["colors"]} for p in matches]}


def find_catalog_products(category: str | None = None, budget_inr: int | None = None) -> list[dict[str, Any]]:
    if settings.data_backend.lower() in {"postgres", "auto"}:
        try:
            rows = query_all(
                "SELECT product_id AS id, sku, name, category, price_inr, stock, active FROM products "
                "WHERE active=true AND (%s IS NULL OR lower(category)=lower(%s)) AND (%s IS NULL OR price_inr<=%s) "
                "ORDER BY price_inr",
                (category, category, budget_inr, budget_inr),
            )
            enriched = []
            for row in rows:
                enriched.append({**(find_product(row["id"]) or {}), **row})
            return enriched
        except Exception:
            if settings.data_backend.lower() == "postgres":
                return []
    if budget_inr is not None:
        return products_under_budget(category, budget_inr)
    products = load_products()
    if category:
        products = [product for product in products if product["category"].lower() == category.lower()]
    return sorted(products, key=lambda p: p["price_inr"])
