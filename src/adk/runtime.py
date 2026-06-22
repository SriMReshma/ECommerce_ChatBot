"""Google ADK Runner adapter for live model mode."""

from __future__ import annotations

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.adk.agents import root_agent

_SESSION_SERVICE = InMemorySessionService()
_RUNNER = Runner(app_name="ecombot-capstone", agent=root_agent, session_service=_SESSION_SERVICE, auto_create_session=True)


async def run_adk_turn(message: str, user_id: str, session_id: str) -> str:
    content = types.Content(role="user", parts=[types.Part(text=message)])
    final_text = ""
    async for event in _RUNNER.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            text_parts = [part.text for part in event.content.parts if getattr(part, "text", None)]
            if text_parts:
                final_text = "".join(text_parts)
    return final_text
