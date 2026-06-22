"""LangSmith tracing helpers for agent turns."""

from __future__ import annotations

from dataclasses import asdict

from langsmith import traceable, tracing_context

from src.config.settings import settings
from src.shared.models import AgentResponse, SessionState


@traceable(name="ecombot-agent-turn", run_type="chain")
async def traced_turn(executor, message: str, state: SessionState) -> AgentResponse:
    return await executor(message, state)


async def run_with_langsmith(executor, message: str, state: SessionState) -> AgentResponse:
    enabled = settings.langsmith_tracing and bool(settings.langsmith_api_key)
    with tracing_context(
        enabled=enabled,
        project_name=settings.langsmith_project,
        tags=["ecombot", settings.runtime_mode],
        metadata={"session_id": state.session_id, "user_id": state.user_id},
    ):
        return await traced_turn(executor, message, state)


def trace_metadata(response: AgentResponse) -> dict:
    payload = asdict(response)
    return {key: payload[key] for key in ("agent", "intent", "route", "model", "cost_usd", "sources", "tool_calls")}
