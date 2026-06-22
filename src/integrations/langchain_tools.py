"""LangChain StructuredTool definitions used by the capstone runtime."""

from __future__ import annotations

from langchain_core.tools import StructuredTool

from src.rag.langchain_rag import get_rag_chain
from src.tools.order_tools import cancel_order, get_invoice, get_order_status
from src.tools.product_tools import check_stock, lookup_product


def search_knowledge(query: str, top_k: int = 4) -> list[dict]:
    """Search product, FAQ, and policy documents in ChromaDB."""
    return get_rag_chain().search(query, top_k)


LANGCHAIN_TOOLS = [
    StructuredTool.from_function(get_order_status, name="get_order_status", description="Get a validated ecommerce order status."),
    StructuredTool.from_function(cancel_order, name="cancel_order", description="Cancel an eligible ecommerce order."),
    StructuredTool.from_function(get_invoice, name="get_invoice", description="Get an invoice URL for an order."),
    StructuredTool.from_function(lookup_product, name="lookup_product", description="Look up a product by ID, SKU, or exact name."),
    StructuredTool.from_function(check_stock, name="check_stock", description="Check live product inventory."),
    StructuredTool.from_function(search_knowledge, name="search_ecombot_knowledge", description="Retrieve grounded ecommerce knowledge from ChromaDB."),
]

TOOLS_BY_NAME = {tool.name: tool for tool in LANGCHAIN_TOOLS}
