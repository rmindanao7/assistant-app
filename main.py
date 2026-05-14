from __future__ import annotations

import logging
import uuid

from app.memory.db import init_db
from app.conversation.controller import respond

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

def main() -> None:
    init_db()
    session_id = str(uuid.uuid4())[:8]
    print(f"Session: {session_id} (type 'exit' to quit)")

    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        out = respond(session_id, user)
        print("\nAssistant:", out, "\n")

if __name__ == "__main__":
    main()