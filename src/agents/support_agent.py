"""Support Agent for orders, tools, inventory, and grounded FAQ responses."""

from __future__ import annotations

import re

from src.gateway.routing import classify_route
from src.rag.retriever import retrieve
from src.shared.models import AgentResponse, SessionState
from src.tools.order_tools import cancel_order, get_invoice, get_order_status
from src.tools.product_tools import check_stock, list_variants, lookup_product

ORDER_RE = re.compile(r"\bORD-[0-9A-Z]{3,}\b", re.I)
PRODUCT_RE = re.compile(r"\b(PRD-[0-9A-Z]{3,}|PHONE-[0-9A-Z]{2,}|TV-[0-9A-Z]{2,}|DECODER-[0-9A-Z]{1,}|ACC-[0-9A-Z]{2,})\b", re.I)
GENERIC_PRODUCT_RE = re.compile(r"\b[A-Z]{2,12}-[A-Z0-9-]{2,40}\b", re.I)


class SupportAgent:
    name = "Support Agent"

    def handle(self, text: str, state: SessionState | None = None, intent: str | None = None) -> AgentResponse:
        state = state or SessionState()
        decision = classify_route(text)
        trace = [f"route={decision.route}", decision.reason]
        lowered = text.lower()

        name = _extract_name(text)
        if name:
            state.customer_name = name
            return _response(f"Hi {name}, I saved your name for this session.", "save_name", decision, trace)
        if "cancel" in lowered:
            return self._cancel(text, state, decision, trace)
        if "invoice" in lowered or "bill" in lowered:
            return self._invoice(text, state, decision, trace)
        if "stock" in lowered or "available" in lowered or "variant" in lowered:
            return self._inventory(text, state, decision, trace)
        if any(word in lowered for word in ("warranty", "return", "refund", "delivery", "shipping", "setup")):
            return self._grounded_answer(text, decision, trace)
        if any(word in lowered for word in ("order", "track", "status", "eta", "ord-")):
            return self._order(text, state, decision, trace)
        if any(word in lowered for word in ("product", "price", "phone", "tv", "decoder", "charger", "prd-")):
            return self._product(text, state, decision, trace)
        return self._grounded_answer(text, decision, trace)

    def _order(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        order_id = _extract_order_id(text, state)
        if not order_id:
            return _response("Please share an order ID like ORD-001.", "order_status", decision, trace)
        result = get_order_status(order_id)
        tool_call = {"name": "get_order_status", "args": {"order_id": order_id}, "result": result}
        if result.get("ok"):
            state.last_order_id = result["order_id"]
            prefix = f"{state.customer_name}, " if state.customer_name else ""
            return _response(
                f"{prefix}Order {result['order_id']} is {result['status']}. ETA: {result['eta']}. Carrier: {result['carrier']}.",
                "order_status",
                decision,
                trace,
                tool_calls=[tool_call],
                cards=[{"type": "order", **result}],
            )
        return _response(_tool_error(result, "I could not find that order."), "order_status", decision, trace, tool_calls=[tool_call])

    def _cancel(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        order_id = _extract_order_id(text, state)
        if not order_id:
            return _response("Please share the order ID to cancel, such as ORD-002.", "cancel_order", decision, trace)
        result = cancel_order(order_id)
        tool_call = {"name": "cancel_order", "args": {"order_id": order_id}, "result": result}
        return _response(_tool_error(result, result.get("message", "Cancellation could not be completed.")), "cancel_order", decision, trace, tool_calls=[tool_call])

    def _invoice(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        order_id = _extract_order_id(text, state)
        if not order_id:
            return _response("Please share the order ID for the invoice.", "invoice", decision, trace)
        result = get_invoice(order_id)
        tool_call = {"name": "get_invoice", "args": {"order_id": order_id}, "result": result}
        if result.get("ok"):
            return _response(f"Invoice for {result['order_id']}: {result['invoice_url']}", "invoice", decision, trace, tool_calls=[tool_call])
        return _response(_tool_error(result, "I could not find that invoice."), "invoice", decision, trace, tool_calls=[tool_call])

    def _inventory(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        key = _extract_product_key(text, state)
        if not key:
            return _response("Please share a product name or SKU to check inventory.", "inventory", decision, trace)
        if "variant" in text.lower():
            result = list_variants(key)
            tool_name = "list_variants"
        else:
            result = check_stock(key)
            tool_name = "check_stock"
        tool_call = {"name": tool_name, "args": {"product": key}, "result": result}
        if result.get("ok") and tool_name == "check_stock":
            state.last_product_id = result["product_id"]
            return _response(f"{result['name']} has {result['stock']} units in stock.", "inventory", decision, trace, tool_calls=[tool_call])
        if result.get("ok"):
            return _response(f"Variants/colors: {result}", "inventory", decision, trace, tool_calls=[tool_call])
        return _response("I could not find that inventory item.", "inventory", decision, trace, tool_calls=[tool_call])

    def _product(self, text: str, state: SessionState, decision, trace: list[str]) -> AgentResponse:
        key = _extract_product_key(text, state)
        if not key:
            return _response("Please share a product name or product ID such as PRD-101.", "product_lookup", decision, trace)
        result = lookup_product(key)
        tool_call = {"name": "lookup_product", "args": {"product": key}, "result": result}
        if result.get("ok"):
            state.last_product_id = result["id"]
            return _response(
                f"{result['name']} costs Rs {result['price_inr']}. It is best for {result['best_for']}. Stock: {result['stock']}.",
                "product_lookup",
                decision,
                trace,
                tool_calls=[tool_call],
                sources=[result["id"]],
                cards=[{"type": "product", **result}],
            )
        return _response("I could not find that product in the catalog.", "product_lookup", decision, trace, tool_calls=[tool_call])

    def _grounded_answer(self, text: str, decision, trace: list[str]) -> AgentResponse:
        chunks = [chunk for chunk in retrieve(text) if chunk["type"] in {"faq", "document"}]
        if not chunks:
            return _response("I could not find grounded information for that in the current knowledge base.", "grounded_support", decision, trace)
        best = chunks[0]
        data = best["data"]
        answer = data.get("answer") or data.get("text")
        source = data.get("id") or data.get("source_file") or best["source"]
        if data.get("page"):
            source = f"{source}:p{data['page']}"
        return _response(answer, "grounded_support", decision, [*trace, f"source={source}"], sources=[source])


def _response(text: str, intent: str, decision, trace: list[str], tool_calls=None, cards=None, sources=None) -> AgentResponse:
    return AgentResponse(
        text=text,
        agent="Support Agent",
        intent=intent,
        model=decision.model,
        route=decision.route,
        trace=trace,
        tool_calls=tool_calls or [],
        cards=cards or [],
        sources=sources or [],
        cost_usd=0.0005 if decision.route == "fast-faq" else 0.002,
    )


def _extract_order_id(text: str, state: SessionState) -> str | None:
    match = ORDER_RE.search(text or "")
    return match.group(0).upper() if match else state.last_order_id


def _extract_product_key(text: str, state: SessionState) -> str | None:
    match = PRODUCT_RE.search(text or "")
    if match:
        return match.group(0).upper()
    generic_match = GENERIC_PRODUCT_RE.search(text or "")
    if generic_match:
        return generic_match.group(0).upper()
    for chunk in retrieve(text):
        if chunk["type"] == "product":
            return chunk["data"]["id"]
    return state.last_product_id


def _extract_name(text: str) -> str | None:
    match = re.search(r"\bmy name is ([A-Za-z][A-Za-z -]{1,40})", text or "", re.I)
    return match.group(1).strip().title() if match else None


def _tool_error(result: dict, fallback: str) -> str:
    if result.get("ok"):
        return result.get("message", "Done.")
    if result.get("error_type") == "timeout":
        return "The backend service timed out. Please try again shortly."
    if result.get("error_type") == "validation":
        return result.get("message", fallback)
    if result.get("error_type") == "not_allowed":
        return result.get("message", fallback)
    if result.get("error_type") == "not_found":
        return fallback
    return result.get("message", fallback)


root_agent = SupportAgent()
