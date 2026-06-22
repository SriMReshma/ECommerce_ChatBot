from src.gateway.routing import classify_route


def test_fast_route_for_simple_support():
    decision = classify_route("Where is my order ORD-001?")
    assert decision.route == "fast-faq"


def test_deep_route_for_recommendation():
    decision = classify_route("Compare Samsung Galaxy A55 vs Redmi Note 13")
    assert decision.route == "deep-support"

