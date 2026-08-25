
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class EvidenceLedger:
    """
    Append-only local evidence ledger.
    This is project memory for the autonomous layer, not a replacement
    for REOS_CONTROL_CENTER state.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        payload = dict(record)
        payload.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
