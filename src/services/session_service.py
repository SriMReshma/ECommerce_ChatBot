"""Redis-backed session snapshots with a local fallback."""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from threading import RLock

from src.config.settings import settings
from src.shared.models import SessionState

_LOCAL_SESSIONS: dict[str, dict] = {}
_LOCK = RLock()


def _client():
    try:
        import redis
    except ImportError as exc:
        raise RuntimeError("Install redis for Redis session snapshots.") from exc
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def _from_dict(payload: dict, session_id: str) -> SessionState:
    allowed = {item.name for item in fields(SessionState)}
    values = {key: value for key, value in payload.items() if key in allowed}
    values.setdefault("session_id", session_id)
    return SessionState(**values)


def save_session(state: SessionState) -> str:
    payload = asdict(state)
    if settings.session_backend.lower() in {"redis", "auto"}:
        try:
            _client().set(
                f"ecombot:session:{state.session_id}",
                json.dumps(payload),
                ex=settings.session_ttl_seconds,
            )
            return "redis"
        except Exception:
            if settings.session_backend.lower() == "redis":
                raise
    with _LOCK:
        _LOCAL_SESSIONS[state.session_id] = payload
    return "memory"


def load_session(session_id: str) -> SessionState:
    if settings.session_backend.lower() in {"redis", "auto"}:
        try:
            raw = _client().get(f"ecombot:session:{session_id}")
            if raw:
                return _from_dict(json.loads(raw), session_id)
        except Exception:
            if settings.session_backend.lower() == "redis":
                raise
    with _LOCK:
        payload = _LOCAL_SESSIONS.get(session_id)
    return _from_dict(payload, session_id) if payload else SessionState(session_id=session_id)


def session_backend_status() -> str:
    if settings.session_backend.lower() == "memory":
        return "memory"
    try:
        return "redis" if _client().ping() else "memory"
    except Exception:
        return "memory-fallback"
