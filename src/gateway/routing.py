"""Route prompts to LiteLLM logical model groups."""

from __future__ import annotations

from dataclasses import dataclass

from src.config.settings import settings

DEEP_SIGNALS = {
    "compare",
    "recommend",
    "which is better",
    "tradeoff",
    "complaint",
    "refund rejected",
    "warranty denied",
    "step by step",
    "best option",
    "too expensive",
    "another option",
}

FAST_SIGNALS = {
    "where is my order",
    "track order",
    "return policy",
    "warranty",
    "shipping",
    "delivery",
    "price",
    "stock",
    "hello",
    "hi",
}


@dataclass(frozen=True)
class RouteDecision:
    route: str
    model: str
    reason: str
    fallback_used: bool = False


def classify_route(prompt: str) -> RouteDecision:
    text = (prompt or "").lower().strip()
    if settings.simulate_primary_timeout or "simulate primary timeout" in text:
        return RouteDecision(
            route="fallback",
            model=settings.fallback_model,
            reason="primary route unavailable; fallback selected",
            fallback_used=True,
        )
    if len(text.split()) >= 35 or any(signal in text for signal in DEEP_SIGNALS):
        return RouteDecision(settings.deep_route, settings.deep_model, "deep-support signal matched")
    if any(signal in text for signal in FAST_SIGNALS):
        return RouteDecision(settings.fast_route, settings.fast_model, "fast-faq signal matched")
    return RouteDecision(settings.fast_route, settings.fast_model, "default support route")

