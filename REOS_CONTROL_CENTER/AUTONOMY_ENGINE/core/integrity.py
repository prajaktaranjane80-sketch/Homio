
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

class IntegrityEngine:
    """
    Read-only integrity engine.
    Does not repair or modify project state.
    """

    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path

    def load_state(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    @staticmethod
    def canonical_hash(value: Any) -> str:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def state_hash(self) -> str:
        return self.canonical_hash(self.load_state())

    def basic(self) -> list[dict[str, str]]:
        try:
            state = self.load_state()
        except Exception as exc:
            return [{"status": "BLOCK", "check": "STATE_LOAD", "message": str(exc)}]

        seq = state.get("execution_plan", {}).get("authoritative_sequence", [])
        current_gate = state.get("execution", {}).get("current_gate")
        current = [
            x for x in seq
            if isinstance(x, dict) and x.get("status") == "CURRENT"
        ]

        checks = []

        if len(current) != 1:
            checks.append({
                "status": "BLOCK",
                "check": "CURRENT_GATE_COUNT",
                "message": f"Expected 1 CURRENT gate, found {len(current)}.",
            })
        else:
            plan_gate = current[0].get("gate")
            if plan_gate != current_gate:
                checks.append({
                    "status": "BLOCK",
                    "check": "CURRENT_GATE_ALIGNMENT",
                    "message": f"execution.current_gate={current_gate}; plan CURRENT={plan_gate}.",
                })
            else:
                checks.append({
                    "status": "PASS",
                    "check": "CURRENT_GATE_ALIGNMENT",
                    "message": f"Current gate aligned: {current_gate}.",
                })

        return checks
