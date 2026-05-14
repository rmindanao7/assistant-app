from __future__ import annotations
from typing import List

def chunk_text(text: str, *, max_chars: int = 800, overlap: int = 120) -> List[str]:
    """
    Deterministic overlapping chunking with safety guards.

    Fixes infinite-loop when text length <= overlap or when end - overlap does not advance.
    """
    text = text.strip()
    if not text:
        return []

    # Guard: overlap must be smaller than max_chars
    overlap = max(0, min(overlap, max_chars - 1)) if max_chars > 1 else 0

    chunks: List[str] = []
    i = 0
    n = len(text)

    while i < n:
        end = min(i + max_chars, n)
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)

        # If we reached the end, stop (prevents infinite loop on short docs)
        if end >= n:
            break

        # Compute next start; ensure progress
        next_i = end - overlap
        if next_i <= i:
            next_i = end  # force forward progress
        i = next_i

    return chunks