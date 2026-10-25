"""Read-only, shared state checks for guarded HOMIO transitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
STATE_PATH = REPOSITORY_ROOT / "REOS_CONTROL_CENTER/data/state.json"

EXPECTED_CORE008_CRITERIA = {
    "CORE-008-AC01": "PENDING",
    "CORE-008-AC02": "VERIFIED",
    "CORE-008-AC03": "VERIFIED",
    "CORE-008-AC04": "PENDING",
    "CORE-008-AC05": "PENDING",
    "CORE-008-AC06": "PENDING",
}


def read_canonical_state() -> dict[str, Any]:
    """Read canonical state without changing it."""
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("Canonical state root must be an object.")
    return state


def state_indexes(
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Return CORE-008 gate, indexed subtasks, and criterion statuses."""
    gate = state.get("gate_plans", {}).get("CORE-008", {})
    subtasks = {
        item.get("id"): item for item in gate.get("subtasks", [])
    }
    criteria = {
        item.get("id"): item.get("status")
        for item in gate.get("criteria_state", [])
    }
    return gate, subtasks, criteria


def require_core008_criteria_baseline(state: dict[str, Any]) -> None:
    """Fail closed if the reviewed AC status baseline has drifted."""
    _gate, _subtasks, criteria = state_indexes(state)
    if criteria != EXPECTED_CORE008_CRITERIA:
        raise ValueError(
            "CORE-008 acceptance-criterion baseline changed: "
            f"{criteria!r}"
        )
