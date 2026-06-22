"""Input guardrail for prompt injection and data-exfiltration attempts."""

from __future__ import annotations

import re

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ignore (all )?(previous|prior) instructions", re.I), "prompt injection"),
    (re.compile(r"system prompt|developer message|hidden instruction", re.I), "system prompt extraction"),
    (re.compile(r"you are now|act as a different|new role", re.I), "role override"),
    (re.compile(r"api key|environment variable|\.env|secret|password", re.I), "data exfiltration"),
]


def inspect_input(text: str) -> tuple[bool, str | None]:
    for pattern, reason in PATTERNS:
        if pattern.search(text or ""):
            return False, reason
    return True, None

