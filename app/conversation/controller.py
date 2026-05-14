from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Dict

from app.llm.lmstudio_client import chat
from app.memory import db, gate, semantic
from app.memory.utils import content_hash, normalize

logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_system_prompt(top_mem: List[str], sem_mem: List[str]) -> str:
    """
    Keep prompt short to reduce latency on T480.
    """
    lines: List[str] = []
    lines.append("You are a persistent local assistant.")
    lines.append("Use the memory below as facts. If something is not in memory, do not claim you remember it.")
    lines.append("")
    if top_mem:
        lines.append("=== Top Memory (high importance) ===")
        lines.extend(f"- {m}" for m in top_mem[:8])
        lines.append("")
    if sem_mem:
        lines.append("=== Related Memory (semantic recall) ===")
        lines.extend(f"- {m}" for m in sem_mem[:6])
        lines.append("")
    lines.append("Be concise and helpful.")
    return "\n".join(lines)


def respond(session_id: str, user_text: str) -> str:
    user_text_n = normalize(user_text)
    ts = _iso_now()

    # Persist turn (always)
    db.add_turn(session_id, "user", user_text_n, ts)

    # Recall memory for prompt
    top_mem = db.top_memories(limit=12)
    sem_mem = semantic.search(user_text_n, k=6)

    system_prompt = _build_system_prompt(top_mem, sem_mem)
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text_n},
    ]

    assistant_text = chat(messages, temperature=0.6, max_tokens=140, timeout_s=300)

    # Persist assistant turn
    db.add_turn(session_id, "assistant", assistant_text, _iso_now())

    # Memory gating (store only important user statements)
    candidates = gate.extract_candidates(user_text_n)
    for cand in candidates:
        s, reasons = gate.score(cand)
        if gate.should_store(s, threshold=0.60):
            mh = content_hash(cand.content)
            inserted = db.upsert_memory(
                mem_hash=mh,
                kind=cand.kind,
                content=cand.content,
                importance=s,
                source=cand.source,
                created_ts=ts,
                last_seen_ts=_iso_now(),
                meta={"reasons": reasons},
            )
            # Update semantic store for retrieval
            semantic.upsert(mh, cand.content)

            logger.info("Stored memory kind=%s score=%.2f inserted=%s reasons=%s",
                        cand.kind, s, inserted, reasons)
        else:
            logger.info("Skipped memory kind=%s score=%.2f reasons=%s",
                        cand.kind, s, reasons)

    return assistant_text