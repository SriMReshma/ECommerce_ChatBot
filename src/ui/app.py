"""Chainlit UI entrypoint for the eComBot capstone."""

from __future__ import annotations

import chainlit as cl

from src.services.session_service import load_session, session_backend_status
from src.ui.chainlit_handlers import build_sidebar_sections, build_ui_payload_async, card_markdown


def _sidebar_elements(sections: list[tuple[str, str, str]]) -> list[cl.Text]:
    return [
        cl.Text(
            name=title,
            content=content,
            display="side",
            language=language,
        )
        for title, content, language in sections
    ]


async def _open_debug_sidebar(sections: list[tuple[str, str, str]]) -> None:
    sidebar_open_count = (cl.user_session.get("sidebar_open_count") or 0) + 1
    cl.user_session.set("sidebar_open_count", sidebar_open_count)
    await cl.ElementSidebar.set_title("Agent Debug Panel")
    await cl.ElementSidebar.set_elements(
        _sidebar_elements(sections),
        key=f"agent-debug-panel-{sidebar_open_count}",
    )


@cl.on_chat_start
async def on_chat_start() -> None:
    session_id = getattr(cl.context.session, "id", "chainlit-session")
    state = load_session(session_id)
    cl.user_session.set("state", state)
    await cl.Message(
        content=(
            "Welcome to ADK Capstone eComBot. Ask about orders, invoices, "
            "returns, warranty, product details, inventory, or recommendations. "
            f"Session memory: {session_backend_status()}."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    state = cl.user_session.get("state")
    if state is None:
        session_id = getattr(cl.context.session, "id", "chainlit-session")
        state = load_session(session_id)
        cl.user_session.set("state", state)

    payload = await build_ui_payload_async(message.content, state)
    answer, reasoning, details, response = payload["answer"], payload["reasoning"], payload["details"], payload["response"]
    sections = build_sidebar_sections(reasoning, details)
    cl.user_session.set("last_debug_sections", sections)
    elements = []
    if response:
        for card in response.cards:
            title, content = card_markdown(card)
            elements.append(cl.Text(name=title, content=content, display="inline", language="markdown"))
        if response.sources:
            elements.append(cl.Text(name="Grounding Sources", content="\n".join(f"- {source}" for source in response.sources), display="inline", language="markdown"))
        badge = f"{response.agent} | {response.route} | {response.model} | ${response.cost_usd:.4f}"
        answer = f"**Blocked**  \n{answer}" if response.intent == "blocked" else answer
        answer = f"{answer}\n\n`{badge}`"
    await cl.Message(
        content=answer,
        elements=elements,
        actions=[
            cl.Action(
                name="show_debug_panel",
                label="Show Debug Panel",
                tooltip="Open the latest reasoning and structured trace in the sidebar.",
                icon="panel-right-open",
                payload={},
            )
        ],
    ).send()

    await _open_debug_sidebar(sections)


@cl.action_callback("show_debug_panel")
async def show_debug_panel(action: cl.Action) -> None:
    sections = cl.user_session.get("last_debug_sections") or []
    if not sections:
        await cl.Message(content="No debug details are available yet.").send()
        return

    await _open_debug_sidebar(sections)
