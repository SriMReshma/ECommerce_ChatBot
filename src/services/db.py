"""PostgreSQL connection-pool and query helpers."""

from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Iterator

from src.config.settings import settings


@lru_cache(maxsize=1)
def _pool():
    try:
        import psycopg2.pool
        import psycopg2.extras
    except ImportError as exc:
        raise RuntimeError("Install psycopg2-binary for PostgreSQL-backed tools.") from exc
    return psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=8,
        dsn=settings.postgres_dsn,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


@contextmanager
def get_connection() -> Iterator[Any]:
    pool = _pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()


def healthcheck() -> bool:
    try:
        return query_one("SELECT 1 AS ok") == {"ok": 1}
    except Exception:
        return False


def ensure_schema() -> None:
    execute("ALTER TABLE session_history ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'anonymous'")
    execute("ALTER TABLE session_history ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb")
    execute("CREATE INDEX IF NOT EXISTS idx_session_history_session_created ON session_history(session_id, created_at)")
