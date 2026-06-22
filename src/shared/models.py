"""Structured response and session models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResponse:
    text: str
    agent: str
    intent: str
    model: str
    route: str
    trace: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    cards: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    reflection: str | None = None
    cost_usd: float = 0.0


@dataclass
class SessionState:
    session_id: str = "local-session"
    user_id: str = "anonymous"
    customer_name: str | None = None
    last_order_id: str | None = None
    last_product_id: str | None = None
    last_agent: str | None = None
    last_intent: str | None = None
    last_lookup_key: str | None = None
    total_cost_usd: float = 0.0
    turns: list[dict[str, Any]] = field(default_factory=list)
