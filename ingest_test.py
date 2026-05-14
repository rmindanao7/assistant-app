from pathlib import Path
from app.ingest.indexer import index_document

count = index_document(Path("docs/sample.txt"))
print(f"Indexed {count} chunks")