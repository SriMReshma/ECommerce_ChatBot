"""Sales Agent with Day 09 ReAct reasoning and reflection."""

from __future__ import annotations

import re
from typing import Any

from src.gateway.routing import classify_route
from src.rag.retriever import find_product, load_products, retrieve
from src.shared.models import AgentResponse, SessionState
from src.tools.product_tools import check_stock, find_catalog_products

BUDGET_RE = re.compile(r"(?:under|below|less than|budget(?: is| of)?|rs\.?)\s*(?:rs\.?\s*)?([0-9][0-9,]*)", re.I)


class SalesAgent:
    name = "Sales Agent"

    def handle(self, text: str, state: SessionState | None = None) -> AgentResponse:
        state = state or SessionState()
        decision = classify_route(text)
        trace = [f"route={decision.route}", decision.reason]
        lowered = text.lower()
        if _is_rejection(lowered):
            return self._reflect(text, state, decision, trace)
        if "compare" in lowered or " vs " in lowered:
            return self._compare(text, state, decision, trace)
        return self._recommend(text, state, decision, trace)

    def _recommend(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        budget = _extract_budget(text) or 25000
        category = _extract_category(text) or "phone"
        candidates = [p for p in find_catalog_products(category, budget) if p["stock"] > 0]
        reasoning = [
            f"Thought: User needs a {category} recommendation within Rs {budget}.",
            f"Action: Filter catalog by category={category}, price<=Rs {budget}, and in-stock items.",
            f"Observation: Found {len(candidates)} matching products.",
            "Thought: Rank by rating, stock, pros, cons, and best-fit description.",
        ]
        if not candidates:
            return _sales_response(f"I could not find an in-stock {category} under Rs {budget}.", "recommendation", decision, trace, reasoning)
        ranked = sorted(candidates, key=lambda p: (p["rating"], p["stock"], -p["price_inr"]), reverse=True)
        best = ranked[0]
        state.last_product_id = best["id"]
        reasoning.append(f"Final: Recommend {best['name']} because it best matches the budget and fit.")
        alternatives = ranked[1:3]
        alt_text = "; ".join(f"{p['name']} at Rs {p['price_inr']}" for p in alternatives)
        text_out = f"My recommendation is {best['name']} at Rs {best['price_inr']}. It is best for {best['best_for']}."
        if alt_text:
            text_out += f" Alternatives: {alt_text}."
        return _sales_response(text_out, "recommendation", decision, trace, reasoning, [_product_card(best), *[_product_card(p) for p in alternatives]], [best["id"], *[p["id"] for p in alternatives]])

    def _compare(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        products = _extract_products(text)
        reasoning = [
            "Thought: User asked for a comparison.",
            "Action: Identify product records from catalog and RAG matches.",
            f"Observation: Found {len(products)} product records.",
        ]
        if len(products) < 2:
            return _sales_response("Please name two products to compare, for example Samsung Galaxy A55 vs Redmi Note 13.", "comparison", decision, trace, reasoning)
        left, right = products[:2]
        reasoning.extend(["Action: Compare price, features, pros, cons, stock, and fit.", "Final: Return a trade-off recommendation."])
        text_out = (
            f"{left['name']} costs Rs {left['price_inr']} and is best for {left['best_for']}. "
            f"{right['name']} costs Rs {right['price_inr']} and is best for {right['best_for']}. "
            f"Choose {right['name']} for value; choose {left['name']} for {left['pros'][0]} and {left['pros'][1]}."
        )
        return _sales_response(text_out, "comparison", decision, trace, reasoning, [_product_card(left), _product_card(right)], [left["id"], right["id"]])

    def _reflect(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        previous = find_product(state.last_product_id or "")
        budget = _extract_budget(text) or 20000
        candidates = [p for p in find_catalog_products("phone", budget) if p["stock"] > 0 and p["id"] != (previous or {}).get("id")]
        reasoning = [
            "Thought: User rejected the previous recommendation.",
            f"Reflection: Avoid repeating {previous['name'] if previous else 'the previous option'} and adjust constraints.",
            f"Action: Search alternatives under Rs {budget}.",
            f"Observation: Found {len(candidates)} alternative phones.",
        ]
        if not candidates:
            return _sales_response("I could not find a better alternative with those constraints.", "reflection", decision, trace, reasoning, reflection="No suitable alternative found.")
        best = sorted(candidates, key=lambda p: (p["rating"], -p["price_inr"]), reverse=True)[0]
        state.last_product_id = best["id"]
        reasoning.append(f"Final: Recommend adjusted alternative {best['name']}.")
        return _sales_response(
            f"Fair point. I will adjust: choose {best['name']} at Rs {best['price_inr']} instead. It fits {best['best_for']}.",
            "reflection",
            decision,
            trace,
            reasoning,
            [_product_card(best)],
            [best["id"]],
            "Updated recommendation after user rejection.",
        )


def _sales_response(text: str, intent: str, decision, trace: list[str], reasoning=None, cards=None, sources=None, reflection=None) -> AgentResponse:
    return AgentResponse(
        text=text,
        agent="Sales Agent",
        intent=intent,
        model=decision.model,
        route=decision.route,
        trace=trace,
        reasoning=reasoning or [],
        cards=cards or [],
        sources=sources or [],
        reflection=reflection,
        cost_usd=0.002,
    )


def _extract_budget(text: str) -> int | None:
    match = BUDGET_RE.search(text or "")
    return int(match.group(1).replace(",", "")) if match else None


def _extract_category(text: str) -> str | None:
    lowered = (text or "").lower()
    for category in ("phone", "tv", "decoder", "accessory"):
        if category in lowered or (category == "phone" and "mobile" in lowered):
            return category
    return None


def _extract_products(text: str) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    lowered = text.lower()
    for product in load_products():
        name_tokens = {token for token in re.findall(r"[a-z0-9]+", product["name"].lower()) if len(token) > 2}
        if product["id"].lower() in lowered or product["sku"].lower() in lowered or len(name_tokens & set(re.findall(r"[a-z0-9]+", lowered))) >= 2:
            products.append(product)
    for chunk in retrieve(text, top_k=6):
        if chunk["type"] == "product" and chunk["data"] not in products:
            products.append(chunk["data"])
    return products


def _is_rejection(text: str) -> bool:
    return any(phrase in text for phrase in ("don't like", "not good", "too expensive", "another option", "something else", "reject"))


def _product_card(product: dict[str, Any]) -> dict[str, Any]:
    return {"type": "product", "product_id": product["id"], "sku": product["sku"], "name": product["name"], "price_inr": product["price_inr"], "stock": product["stock"], "rating": product["rating"], "features": product["features"], "pros": product["pros"], "cons": product["cons"], "best_for": product["best_for"]}


root_agent = SalesAgent()

