from fastapi.testclient import TestClient

from src.api.app import app


def test_promptfoo_http_contract_returns_structured_response():
    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"message": "Where is my order ORD-001?", "session_id": "http-test", "user_id": "pytest"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "Shipped" in payload["text"]
    assert payload["agent"] == "Support Agent"
    assert payload["tool_calls"][0]["name"] == "get_order_status"
