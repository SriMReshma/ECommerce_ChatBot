"""Deterministic local retrieval over products, FAQ, and ingested PDF chunks."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

from src.config.settings import DATA_DIR, RAG_DATA_DIR, settings


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


@lru_cache(maxsize=1)
def load_products() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "products.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_faq() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "faq.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_document_chunks() -> list[dict[str, Any]]:
    path = RAG_DATA_DIR / "document_index.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def retrieve(query: str, top_k: int = 4) -> list[dict[str, Any]]:
    if settings.use_chromadb:
        try:
            from src.rag.langchain_rag import get_rag_chain

            results = get_rag_chain().search(query, top_k)
            if results:
                return results
        except Exception:
            pass

    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    docs: list[dict[str, Any]] = []
    for product in load_products():
        text = " ".join(
            [
                product["id"],
                product["sku"],
                product["name"],
                product["brand"],
                product["category"],
                str(product["price_inr"]),
                product["best_for"],
                " ".join(product["features"]),
                " ".join(product["pros"]),
                " ".join(product["cons"]),
            ]
        )
        docs.append({"type": "product", "source": product["id"], "text": text, "data": product})

    for faq in load_faq():
        docs.append(
            {
                "type": "faq",
                "source": faq["id"],
                "text": f"{faq['category']} {faq['question']} {faq['answer']} {' '.join(faq.get('keywords', []))}",
                "data": faq,
            }
        )

    for chunk in load_document_chunks():
        docs.append({"type": "document", "source": chunk["id"], "text": chunk["text"], "data": chunk})

    scored: list[tuple[int, dict[str, Any]]] = []
    lowered = query.lower()
    for doc in docs:
        score = len(query_tokens & _tokens(doc["text"]))
        data = doc["data"]
        if data.get("name", "").lower() in lowered:
            score += 6
        if data.get("sku", "").lower() in lowered or data.get("id", "").lower() in lowered:
            score += 7
        if data.get("question", "").lower() in lowered:
            score += 5
        if data.get("section", "").lower() in lowered:
            score += 2
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def find_product(value: str) -> dict[str, Any] | None:
    needle = (value or "").strip().lower()
    if not needle:
        return None
    for product in load_products():
        if needle in {product["id"].lower(), product["sku"].lower(), product["name"].lower()}:
            return product
        name_tokens = _tokens(product["name"])
        if name_tokens and name_tokens.issubset(_tokens(needle)):
            return product
    for chunk in retrieve(value, top_k=3):
        if chunk["type"] == "product":
            return chunk["data"]
    return None


def products_under_budget(category: str | None, budget_inr: int) -> list[dict[str, Any]]:
    products = load_products()
    if category:
        products = [product for product in products if product["category"].lower() == category.lower()]
    return sorted([product for product in products if product["price_inr"] <= budget_inr], key=lambda p: p["price_inr"])
