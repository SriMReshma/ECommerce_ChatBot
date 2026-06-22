"""Dependency-free helpers used by the Chainlit UI."""

from __future__ import annotations

import json
from dataclasses import asdict

from src.runtime.engine import runtime
from src.shared.models import SessionState


def build_ui_response(message: str, state: SessionState) -> tuple[str, str, str]:
    message = (message or "").strip()
    if not message:
        return "Please enter a customer question.", "", "{}"

    response = runtime.handle(message, state)
    return format_ui_response(response)


async def build_ui_response_async(message: str, state: SessionState) -> tuple[str, str, str]:
    message = (message or "").strip()
    if not message:
        return "Please enter a customer question.", "", "{}"
    response = await runtime.handle_async(message, state)
    return format_ui_response(response)


async def build_ui_payload_async(message: str, state: SessionState) -> dict:
    message = (message or "").strip()
    if not message:
        return {"answer": "Please enter a customer question.", "reasoning": "", "details": "{}", "response": None}
    response = await runtime.handle_async(message, state)
    answer, reasoning, details = format_ui_response(response)
    return {"answer": answer, "reasoning": reasoning, "details": details, "response": response}


def format_ui_response(response) -> tuple[str, str, str]:
    reasoning = "\n".join(f"- {step}" for step in response.reasoning)
    details = json.dumps(
        {
            "agent": response.agent,
            "intent": response.intent,
            "route": response.route,
            "model": response.model,
            "sources": response.sources,
            "cards": response.cards,
            "tool_calls": response.tool_calls,
            "trace": response.trace,
            "reflection": response.reflection,
            "cost_usd": response.cost_usd,
        },
        indent=2,
    )
    return response.text, reasoning, details


def card_markdown(card: dict) -> tuple[str, str]:
    if card.get("type") == "product":
        title = card.get("name", "Product")
        body = (
            f"**Rs {card.get('price_inr', 'N/A')}**  \n"
            f"Stock: **{card.get('stock', 'N/A')}**  \n"
            f"Rating: **{card.get('rating', 'N/A')}**  \n"
            f"Best for: {card.get('best_for', 'N/A')}"
        )
        return title, body
    if card.get("type") == "order":
        title = f"Order {card.get('order_id', '')}"
        body = f"Status: **{card.get('status', 'N/A')}**  \nETA: {card.get('eta', 'N/A')}  \nCarrier: {card.get('carrier', 'N/A')}"
        return title, body
    return card.get("type", "Result").title(), f"```json\n{json.dumps(card, indent=2)}\n```"


def build_sidebar_sections(reasoning: str, details: str) -> list[tuple[str, str, str]]:
    sections = []
    if reasoning:
        sections.append(("Agent Reasoning", reasoning, "markdown"))
    sections.append(("Trace and Structured Output", details, "json"))
    return sections
