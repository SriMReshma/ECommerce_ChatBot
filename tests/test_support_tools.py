from src.agents.orchestrator import Orchestrator
from src.shared.models import SessionState
from src.tools.order_tools import get_order_status
from src.tools.product_tools import check_stock


def test_order_status_success():
    result = get_order_status("ORD-001")
    assert result["ok"] is True
    assert result["status"] == "Shipped"


def test_support_agent_uses_order_context():
    bot = Orchestrator()
    state = SessionState()
    first = bot.handle("Hi, my name is Priya", state)
    second = bot.handle("Where is my order ORD-001?", state)
    assert first.intent == "save_name"
    assert "Priya" in second.text
    assert second.tool_calls[0]["name"] == "get_order_status"


def test_inventory_stock():
    result = check_stock("PRD-102")
    assert result["ok"] is True
    assert result["stock"] > 0

