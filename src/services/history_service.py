"""Durable conversation history helpers."""

from __future__ import annotations

import json
from typing import Any

from src.config.settings import settings
from src.services.db import execute, query_all, query_one

_LOCAL_HISTORY: list[dict[str, Any]] = []


def save_turn(
    session_id: str,
    role: str,
    content: str,
    tool_calls: list[dict[str, Any]] | None = None,
    user_id: str = "anonymous",
    metadata: dict[str, Any] | None = None,
) -> str:
    record = {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "tool_calls": tool_calls or [],
        "metadata": metadata or {},
    }
    if settings.history_backend.lower() in {"postgres", "auto"}:
        try:
            execute(
                "INSERT INTO session_history (session_id, user_id, role, content, tool_calls, metadata) "
                "VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)",
                (
                    session_id,
                    user_id,
                    role,
                    content,
                    json.dumps(tool_calls or []),
                    json.dumps(metadata or {}),
                ),
            )
            return "postgres"
        except Exception:
            if settings.history_backend.lower() == "postgres":
                raise
    _LOCAL_HISTORY.append(record)
    return "memory"


def latest_turn(session_id: str) -> dict[str, Any] | None:
    try:
        return query_one(
            "SELECT session_id, user_id, role, content, tool_calls, metadata, created_at "
            "FROM session_history WHERE session_id=%s ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
    except Exception:
        return next((item for item in reversed(_LOCAL_HISTORY) if item["session_id"] == session_id), None)


def conversation(session_id: str) -> list[dict[str, Any]]:
    try:
        return query_all(
            "SELECT session_id, user_id, role, content, tool_calls, metadata, created_at "
            "FROM session_history WHERE session_id=%s ORDER BY created_at",
            (session_id,),
        )
    except Exception:
        return [item for item in _LOCAL_HISTORY if item["session_id"] == session_id]
