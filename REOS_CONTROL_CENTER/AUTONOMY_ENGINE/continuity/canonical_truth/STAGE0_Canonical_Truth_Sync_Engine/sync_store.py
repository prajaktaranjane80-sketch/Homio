from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SyncStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.sync_dir = self.root / "artifacts" / "truth_sync"
        self.sync_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, payload: Any) -> Path:
        path = self.sync_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
