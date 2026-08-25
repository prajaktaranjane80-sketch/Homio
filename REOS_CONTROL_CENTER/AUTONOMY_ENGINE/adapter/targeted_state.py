
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_state(root: Path) -> dict[str, Any]:
    path = root / "data" / "state.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def compact_state(root: Path) -> dict[str, Any]:
    state = load_state(root)
    execution = state.get("execution", {})
    seq = state.get("execution_plan", {}).get("authoritative_sequence", [])
    current = [x for x in seq if isinstance(x, dict) and x.get("status") == "CURRENT"]

    current_gate = execution.get("current_gate")
    current_plan = current[0] if len(current) == 1 else None

    gate_plan = state.get("gate_plans", {}).get(current_gate, {})
    if not isinstance(gate_plan, dict):
        gate_plan = {}

    criteria = gate_plan.get("criteria_state", [])
    subtasks = gate_plan.get("subtasks", [])
    if not isinstance(criteria, list):
        criteria = []
    if not isinstance(subtasks, list):
        subtasks = []

    return {
        "current_gate": current_gate,
        "current_task": execution.get("current_task"),
        "current_subtask": execution.get("current_subtask"),
        "execution_status": execution.get("status"),
        "plan_current": {
            "gate": current_plan.get("gate") if current_plan else None,
            "status": current_plan.get("status") if current_plan else None,
            "name": current_plan.get("name") if current_plan else None,
        },
        "gate_status": gate_plan.get("status"),
        "subtasks": {
            "total": len(subtasks),
            "current": [x.get("id") for x in subtasks if isinstance(x, dict) and x.get("status") in {"CURRENT", "IN_PROGRESS"}],
            "done": [x.get("id") for x in subtasks if isinstance(x, dict) and x.get("status") in {"DONE", "COMPLETE", "COMPLETED"}],
        },
        "criteria": {
            "total": len(criteria),
            "pending": [x.get("id") for x in criteria if isinstance(x, dict) and x.get("status") not in {"VERIFIED"}],
            "verified": [x.get("id") for x in criteria if isinstance(x, dict) and x.get("status") == "VERIFIED"],
        },
    }
