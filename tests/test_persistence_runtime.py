from src.runtime.engine import runtime
from src.services.history_service import conversation
from src.services.session_service import load_session
from src.shared.models import SessionState


def test_runtime_persists_state_and_history_in_configured_backend():
    state = SessionState(session_id="runtime-persistence-test", user_id="pytest")
    response = runtime.handle("Where is my order ORD-001?", state)

    restored = load_session(state.session_id)
    history = conversation(state.session_id)
    assert response.intent == "order_status"
    assert restored.last_order_id == "ORD-001"
    assert [turn["role"] for turn in history[-2:]] == ["user", "assistant"]
