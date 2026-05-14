"""
SQLite persistence for:
- conversation turns (all turns)
- durable memory (gated, scored)
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "assistant.db"


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            mem_hash TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,                -- preference|profile|task|fact|other
            content TEXT NOT NULL,
            importance REAL NOT NULL,          -- 0..1
            source TEXT NOT NULL,              -- user|system|import
            created_ts TEXT NOT NULL,
            last_seen_ts TEXT NOT NULL,
            times_seen INTEGER NOT NULL DEFAULT 1,
            meta_json TEXT NOT NULL DEFAULT '{}'
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_importance ON memories(importance DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_turn_session ON turns(session_id, id);")


def add_turn(session_id: str, role: str, content: str, ts_iso: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO turns(session_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (session_id, role, content, ts_iso),
        )


def get_recent_turns(session_id: str, limit: int = 10) -> List[Tuple[str, str, str]]:
    """
    Returns list of (role, content, ts) newest-last.
    """
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, ts FROM turns WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return list(reversed(rows))


def upsert_memory(
    mem_hash: str,
    kind: str,
    content: str,
    importance: float,
    source: str,
    created_ts: str,
    last_seen_ts: str,
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Insert new memory if hash doesn't exist; otherwise update last_seen/times/importance (max).
    Returns True if inserted, False if updated.
    """
    meta_json = json.dumps(meta or {}, ensure_ascii=False)
    with connect() as conn:
        cur = conn.execute("SELECT id, importance, times_seen FROM memories WHERE mem_hash=?", (mem_hash,))
        row = cur.fetchone()
        if row is None:
            conn.execute(
                """INSERT INTO memories(mem_hash, kind, content, importance, source, created_ts, last_seen_ts, times_seen, meta_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (mem_hash, kind, content, importance, source, created_ts, last_seen_ts, meta_json),
            )
            return True

        mem_id, old_imp, old_seen = row
        new_imp = max(float(old_imp), float(importance))
        conn.execute(
            """UPDATE memories
               SET last_seen_ts=?, times_seen=?, importance=?, meta_json=?
               WHERE id=?""",
            (last_seen_ts, int(old_seen) + 1, new_imp, meta_json, mem_id),
        )
        return False


def top_memories(limit: int = 12) -> List[str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT content FROM memories ORDER BY importance DESC, last_seen_ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [r[0] for r in rows]


def all_memories_for_embedding(limit: int = 2000) -> List[Tuple[int, str, str]]:
    """
    Returns (id, mem_hash, content) for embedding sync.
    """
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, mem_hash, content FROM memories ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [(int(r[0]), str(r[1]), str(r[2])) for r in rows]