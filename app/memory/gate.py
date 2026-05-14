"""
Memory gating:
- Extract candidate memories from user text
- Score importance (0..1)
- Only store if above threshold
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Tuple

from .utils import looks_like_secret, normalize

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MemoryCandidate:
    kind: str     # preference|profile|task|fact|other
    content: str
    source: str = "user"


# Simple patterns for durable info
_RE_NAME = re.compile(r"\b(my name is|i am|i'm)\s+([A-Za-z][A-Za-z\-\s]{1,40})\b", re.I)
_RE_PREF = re.compile(r"\b(i like|i love|i prefer|my favorite|i hate|i dislike)\b", re.I)
_RE_TASK = re.compile(r"\b(remind me|i need to|i have to|please remember|deadline|due|tomorrow|next week|on \w+day)\b", re.I)
_RE_PROFILE = re.compile(r"\b(i work as|my job|i live in|i'm from|my email is|contact me at)\b", re.I)
_RE_FACTISH = re.compile(r"\b(always|never)\b", re.I)


def extract_candidates(user_text: str) -> List[MemoryCandidate]:
    """
    Extract memory candidates from a single user turn.
    Keep this conservative: better to miss than to pollute memory.
    """
    text = normalize(user_text)
    if not text or looks_like_secret(text):
        return []

    cands: List[MemoryCandidate] = []

    # name/profile
    if _RE_NAME.search(text) or _RE_PROFILE.search(text):
        cands.append(MemoryCandidate(kind="profile", content=text))

    # preferences
    if _RE_PREF.search(text):
        cands.append(MemoryCandidate(kind="preference", content=text))

    # tasks/commitments
    if _RE_TASK.search(text):
        cands.append(MemoryCandidate(kind="task", content=text))

    # lightweight fact-ish statements (rarely store unless strong)
    if _RE_FACTISH.search(text) and len(text.split()) >= 8:
        cands.append(MemoryCandidate(kind="fact", content=text))

    return cands


def score(candidate: MemoryCandidate) -> Tuple[float, List[str]]:
    """
    Return (importance_score, reasons).
    Deterministic heuristic scoring. 0..1.
    """
    t = candidate.content.lower()
    reasons: List[str] = []
    s = 0.10  # base

    # kind-based priors
    if candidate.kind == "task":
        s += 0.55; reasons.append("task/commitment")
    elif candidate.kind == "preference":
        s += 0.45; reasons.append("preference")
    elif candidate.kind == "profile":
        s += 0.50; reasons.append("profile")
    elif candidate.kind == "fact":
        s += 0.25; reasons.append("general fact-ish")

    # specificity boosts
    if any(x in t for x in ["my name is", "i am ", "i'm "]):
        s += 0.25; reasons.append("identity marker")
    if any(x in t for x in ["always", "never"]):
        s += 0.10; reasons.append("stable behavior keyword")
    if re.search(r"\b\d{1,2}[:/]\d{1,2}\b", t) or re.search(r"\b\d{4}\b", t):
        s += 0.10; reasons.append("contains date/time/number")

    # length sanity (too short usually noise)
    wc = len(candidate.content.split())
    if wc <= 4:
        s -= 0.25; reasons.append("too short/noisy")

    # secret suppression (hard stop handled earlier but keep safety)
    if looks_like_secret(candidate.content):
        return 0.0, ["looks like secret -> blocked"]

    # clamp
    s = max(0.0, min(1.0, s))
    return s, reasons


def should_store(score_value: float, *, threshold: float = 0.60) -> bool:
    return score_value >= threshold