"""FastAPI endpoint used by integrations and Promptfoo."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.runtime.engine import runtime
from src.services.session_service import load_session

app = FastAPI(title="eComBot Capstone API", version="1.0.0")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = "api-session"
    user_id: str = "promptfoo"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    state = load_session(request.session_id)
    state.user_id = request.user_id
    response = await runtime.handle_async(request.message, state)
    return {
        "text": response.text,
        "agent": response.agent,
        "intent": response.intent,
        "route": response.route,
        "model": response.model,
        "sources": response.sources,
        "tool_calls": response.tool_calls,
        "blocked": response.intent == "blocked",
        "cost_usd": response.cost_usd,
    }
