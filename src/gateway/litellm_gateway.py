"""Live LiteLLM completion and fallback execution."""

from __future__ import annotations

from dataclasses import dataclass

from src.config.settings import settings
from src.gateway.routing import RouteDecision


@dataclass(frozen=True)
class GatewayResult:
    text: str
    model: str
    fallback_used: bool


def _content(response) -> str:
    return str(response.choices[0].message.content or "").strip()


def complete_with_fallback(prompt: str, decision: RouteDecision, grounded_draft: str = "") -> GatewayResult:
    import litellm

    system = (
        "You are eComBot. Answer only electronics ecommerce questions. Preserve all factual values and source "
        "identifiers from the grounded draft. Never invent order, inventory, price, warranty, or policy data."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Customer request: {prompt}\nGrounded draft: {grounded_draft}"},
    ]
    try:
        if settings.simulate_primary_timeout:
            raise TimeoutError("simulated primary timeout")
        response = litellm.completion(model=decision.model, messages=messages, api_key=settings.openrouter_api_key)
        return GatewayResult(_content(response), decision.model, False)
    except Exception:
        response = litellm.completion(model=settings.fallback_model, messages=messages, api_key=settings.openrouter_api_key)
        return GatewayResult(_content(response), settings.fallback_model, True)
