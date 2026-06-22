from src.shared.models import SessionState
from src.ui.chainlit_handlers import build_sidebar_sections, build_ui_response


def test_chainlit_handler_returns_visible_answer_and_trace():
    answer, reasoning, details = build_ui_response("Recommend a phone under Rs 25000", SessionState())

    assert "recommendation" in details
    assert "Samsung Galaxy M35" in answer
    assert reasoning


def test_trace_sections_are_sidebar_ready():
    sections = build_sidebar_sections("- routed to sales", '{"route": "deep-support"}')

    assert sections == [
        ("Agent Reasoning", "- routed to sales", "markdown"),
        ("Trace and Structured Output", '{"route": "deep-support"}', "json"),
    ]
