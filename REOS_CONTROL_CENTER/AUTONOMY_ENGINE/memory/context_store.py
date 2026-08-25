
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

class ContextStore:
    """
    Compact machine context cache.
    Never stores entire source files or conversation history.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, context: dict[str, Any]) -> None:
        self.path.write_text(
            json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
