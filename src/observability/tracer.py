"""JSONL trace logger with LangSmith-style fields but no network dependency."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any

from src.config.settings import PROJECT_ROOT
from src.shared.models import AgentResponse

TRACE_PATH = PROJECT_ROOT / "runtime" / "traces.jsonl"


def _fallback_trace_path() -> Path:
    return Path(tempfile.gettempdir()) / "ecombot_Capstone_GoogleADK" / "traces.jsonl"


def record_trace(session_id: str, user_text: str, response: AgentResponse, latency_ms: float = 0.0) -> dict[str, Any]:
    trace_path = TRACE_PATH
    try:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        trace_path = _fallback_trace_path()
        trace_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "user_text": user_text,
        "agent": response.agent,
        "intent": response.intent,
        "route": response.route,
        "model": response.model,
        "latency_ms": round(latency_ms, 2),
        "tool_calls": response.tool_calls,
        "sources": response.sources,
        "reasoning": response.reasoning,
        "cost_usd": response.cost_usd,
        "response": asdict(response),
    }
    try:
        with trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
    except PermissionError:
        trace_path = _fallback_trace_path()
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        with trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
    return event


def read_traces(limit: int = 20) -> list[dict[str, Any]]:
    trace_path = TRACE_PATH if TRACE_PATH.exists() else _fallback_trace_path()
    if not trace_path.exists():
        return []
    try:
        lines = trace_path.read_text(encoding="utf-8").splitlines()
    except PermissionError:
        fallback_path = _fallback_trace_path()
        if not fallback_path.exists():
            return []
        lines = fallback_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()]
