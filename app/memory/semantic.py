from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CHROMA_DIR = Path("data") / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _client.get_or_create_collection("memories_v1")

# CPU-friendly embedding model
_encoder = SentenceTransformer("all-MiniLM-L6-v2")


def upsert(mem_hash: str, text: str) -> None:
    emb = _encoder.encode(text).tolist()
    # Use id=mem_hash so dedupe is automatic
    _collection.upsert(ids=[mem_hash], documents=[text], embeddings=[emb])


def search(query: str, k: int = 5) -> List[str]:
    emb = _encoder.encode(query).tolist()
    res = _collection.query(query_embeddings=[emb], n_results=k)
    docs = res.get("documents", [[]])[0]
    return [str(d) for d in docs]

def get_encoder():
    """Public getter for the sentence transformer encoder."""
    return _encoder
