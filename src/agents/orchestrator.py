"""Orchestrator that routes support and sales flows."""

from __future__ import annotations

import time

from src.agents.sales_agent import SalesAgent
from src.agents.support_agent import SupportAgent
from src.gateway.routing import classify_route
from src.guardrails.input_guard import inspect_input
from src.guardrails.output_guard import filter_output
from src.observability.tracer import record_trace
from src.shared.models import AgentResponse, SessionState


class Orchestrator:
    def __init__(self) -> None:
        self.support = SupportAgent()
        self.sales = SalesAgent()

    def handle(self, text: str, state: SessionState | None = None) -> AgentResponse:
        state = state or SessionState()
        started = time.perf_counter()
        allowed, reason = inspect_input(text)
        if not allowed:
            decision = classify_route(text)
            response = AgentResponse(
                text=f"Blocked by input guardrail: {reason}. I can help with orders, products, warranty, delivery, returns, or recommendations.",
                agent="Orchestrator",
                intent="blocked",
                model=decision.model,
                route=decision.route,
                trace=[f"input_guard={reason}", decision.reason],
            )
            record_trace(state.session_id, text, response, (time.perf_counter() - started) * 1000)
            return response

        response = self.sales.handle(text, state) if _is_sales_query(text, state) else self.support.handle(text, state)
        filtered, output_reasons = filter_output(response.text)
        if output_reasons:
            response.text = filtered
            response.trace.append(f"output_guard={','.join(sorted(set(output_reasons)))}")
        state.last_agent = response.agent
        state.turns.append({"user": text, "agent": response.agent, "intent": response.intent, "text": response.text})
        record_trace(state.session_id, text, response, (time.perf_counter() - started) * 1000)
        return response


def _is_sales_query(text: str, state: SessionState) -> bool:
    lowered = (text or "").lower()
    if state.last_agent == "Sales Agent" and any(phrase in lowered for phrase in ("another", "something else", "too expensive", "don't like", "not good")):
        return True
    return any(keyword in lowered for keyword in ("recommend", "suggest", "what phone should i buy", "which phone", "best phone", "compare", " vs ", "budget", "under rs", "under 20000"))


root_agent = Orchestrator()
