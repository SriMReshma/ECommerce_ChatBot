"""Output guardrail for accidental PII and unsupported competitor mentions."""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){10}(?!\d)")
COMPETITORS = ("amazon", "flipkart", "croma", "reliance digital")


def filter_output(text: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    filtered = EMAIL_RE.sub("[email redacted]", text)
    if filtered != text:
        reasons.append("pii_email")
    newer = PHONE_RE.sub("[phone redacted]", filtered)
    if newer != filtered:
        reasons.append("pii_phone")
    filtered = newer
    for competitor in COMPETITORS:
        pattern = re.compile(re.escape(competitor), re.I)
        if pattern.search(filtered):
            filtered = pattern.sub("[competitor redacted]", filtered)
            reasons.append("competitor")
    return filtered, reasons

