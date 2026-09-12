from __future__ import annotations

import json
from pathlib import Path


def load_contract(path: Path) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    required = {"layer", "name", "authority", "forbidden_operations"}
    missing = required - set(contract)
    if missing:
        raise ValueError(f"Contract missing keys: {sorted(missing)}")
    return contract
