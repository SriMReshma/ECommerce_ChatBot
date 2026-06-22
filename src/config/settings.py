"""Environment-driven settings for eComBot."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = PROJECT_ROOT / "docs" / "knowledge_base"
RAG_DATA_DIR = PROJECT_ROOT / "src" / "rag" / "data"
_WINDOWS_CHROMA_DIR = Path(tempfile.gettempdir()) / "ecombot-capstone" / "chroma_db"
CHROMA_DIR = Path(
    os.getenv(
        "CHROMA_DIR",
        str(_WINDOWS_CHROMA_DIR if os.name == "nt" and "onedrive" in str(PROJECT_ROOT).lower() else PROJECT_ROOT / "chroma_db"),
    )
)


@dataclass(frozen=True)
class Settings:
    app_name: str = "ADK Capstone eComBot"
    runtime_mode: str = os.getenv("ECOMBOT_RUNTIME_MODE", "deterministic")
    session_backend: str = os.getenv("SESSION_BACKEND", "memory")
    data_backend: str = os.getenv("DATA_BACKEND", "memory")
    history_backend: str = os.getenv("HISTORY_BACKEND", "memory")
    use_chromadb: bool = os.getenv("ECOMBOT_USE_CHROMADB", "true").lower() == "true"
    use_mcp: bool = os.getenv("ECOMBOT_USE_MCP", "false").lower() == "true"
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", "86400"))
    rag_top_k: int = int(os.getenv("ECOMBOT_RAG_TOP_K", "4"))
    fast_route: str = os.getenv("ECOMBOT_FAST_ROUTE", "fast-faq")
    deep_route: str = os.getenv("ECOMBOT_DEEP_ROUTE", "deep-support")
    fast_model: str = os.getenv("ECOMBOT_FAST_MODEL", "openrouter/google/gemini-2.5-flash")
    deep_model: str = os.getenv("ECOMBOT_DEEP_MODEL", "openrouter/openai/gpt-4o-mini")
    fallback_model: str = os.getenv("ECOMBOT_FALLBACK_MODEL", "openrouter/google/gemini-2.5-flash")
    litellm_base_url: str = os.getenv("LITELLM_BASE_URL", "http://127.0.0.1:4000")
    litellm_proxy_api_key: str = os.getenv("LITELLM_PROXY_API_KEY", "sk-ecombot-local")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    simulate_primary_timeout: bool = os.getenv("ECOMBOT_SIMULATE_PRIMARY_TIMEOUT", "false").lower() == "true"
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5433"))
    postgres_db: str = os.getenv("POSTGRES_DB", "ecombot")
    postgres_user: str = os.getenv("POSTGRES_USER", "ecombot")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "ecombot_password")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6380"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "ecombot_redis_password")
    mcp_host: str = os.getenv("MCP_HOST", "127.0.0.1")
    mcp_port: int = int(os.getenv("MCP_PORT", "8775"))
    mcp_url: str = os.getenv("MCP_URL", "http://127.0.0.1:8775/mcp")
    mcp_transport: str = os.getenv("MCP_TRANSPORT", "inprocess")
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "ecombot-capstone")
    langsmith_tracing: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password} host={self.postgres_host} port={self.postgres_port}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    @property
    def live_llm_enabled(self) -> bool:
        return self.runtime_mode.lower() in {"live", "adk", "litellm"} and bool(self.openrouter_api_key)


settings = Settings()
