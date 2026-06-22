from src.agents.orchestrator import Orchestrator
from src.shared.models import SessionState


def test_react_recommendation_has_steps():
    response = Orchestrator().handle("What phone should I buy under Rs 20000?", SessionState())
    assert response.agent == "Sales Agent"
    assert response.intent == "recommendation"
    assert any(step.startswith("Thought:") for step in response.reasoning)
    assert any(step.startswith("Action:") for step in response.reasoning)
    assert any(step.startswith("Observation:") for step in response.reasoning)
    assert response.sources


def test_comparison_is_grounded():
    response = Orchestrator().handle("Compare Samsung Galaxy A55 vs Redmi Note 13", SessionState())
    assert "Samsung Galaxy A55" in response.text
    assert "Redmi Note 13" in response.text
    assert {"PHONE-A55", "PHONE-RN13"}.issubset(set(response.sources))


def test_reflection_after_rejection():
    bot = Orchestrator()
    state = SessionState()
    first = bot.handle("Recommend a phone under Rs 20000", state)
    second = bot.handle("I don't like that, give me another option under Rs 20000", state)
    assert first.agent == "Sales Agent"
    assert second.intent == "reflection"
    assert second.reflection
    assert second.sources[0] != first.sources[0]

