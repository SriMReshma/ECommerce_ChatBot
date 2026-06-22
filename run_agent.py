"""Local CLI runner for eComBot."""

from __future__ import annotations

import argparse

from src.agents.orchestrator import root_agent
from src.evals.eval_runner import run_evals
from src.observability.tracer import read_traces
from src.shared.models import SessionState


SCENARIO = [
    "Hi, my name is Priya.",
    "Where is my order ORD-001?",
    "What is the warranty on the Samsung TV?",
    "What phone should I buy under Rs 20000?",
    "I don't like that, give me another option under Rs 20000.",
]


def run_messages(messages: list[str]) -> None:
    state = SessionState(session_id="cli-session")
    for message in messages:
        response = root_agent.handle(message, state)
        print(f"\nUSER: {message}")
        print(f"{response.agent} [{response.route}/{response.model}]: {response.text}")
        if response.sources:
            print("Sources:", ", ".join(response.sources))
        if response.reasoning:
            print("Reasoning:")
            for step in response.reasoning:
                print(f"  - {step}")
        if response.reflection:
            print("Reflection:", response.reflection)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("messages", nargs="*")
    parser.add_argument("--scenario", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--traces", action="store_true")
    args = parser.parse_args()
    if args.eval:
        passed, total = run_evals()
        raise SystemExit(0 if passed == total else 1)
    if args.traces:
        for trace in read_traces():
            print(trace)
        return
    run_messages(SCENARIO if args.scenario or not args.messages else args.messages)


if __name__ == "__main__":
    main()
