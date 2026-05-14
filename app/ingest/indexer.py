from __future__ import annotations
from pathlib import Path
import uuid

import chromadb

from app.ingest.chunker import chunk_text
from app.memory.semantic import _encoder

# Persistent Chroma client
_client = chromadb.PersistentClient(path="data/chroma")

# Separate collection for documents
_docs = _client.get_or_create_collection("documents_v1")


def index_document(path: Path) -> int:
    """
    Index a text document into the documents_v1 collection.
    Returns the number of chunks indexed.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    text = path.read_text(encoding="utf-8", errors="ignore")
    chunks = chunk_text(text)

    ids = []
    embeddings = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(str(uuid.uuid4()))
        embeddings.append(_encoder.encode(chunk).tolist())
        metadatas.append({
            "source": str(path),
            "chunk": i,
        })

    _docs.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(chunks)