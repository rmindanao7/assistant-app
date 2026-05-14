from __future__ import annotations

import hashlib
import re
from typing import Tuple

_SECRET_PATTERNS = [
    re.compile(r"\b(password|passcode|otp|one[- ]time|token|api[-_ ]key|secret)\b", re.I),
    re.compile(r"\b\d{6}\b"),  # common OTP length
    re.compile(r"sk-[A-Za-z0-9]{16,}"),  # common API key shape
]


def normalize(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def content_hash(text: str) -> str:
    n = normalize(text).lower()
    return hashlib.sha256(n.encode("utf-8")).hexdigest()


def looks_like_secret(text: str) -> bool:
    t = text.strip()
    if len(t) >= 40 and re.search(r"[A-Za-z]", t) and re.search(r"\d", t):
        # long mixed strings are often secrets/tokens
        for p in _SECRET_PATTERNS:
            if p.search(t):
                return True
        # even without keyword, be conservative with long mixed strings
        return True

    for p in _SECRET_PATTERNS:
        if p.search(t):
            return True
    return False
