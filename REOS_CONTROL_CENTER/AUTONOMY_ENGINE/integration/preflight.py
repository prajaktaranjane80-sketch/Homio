
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapter.controller_adapter import ControllerAdapter
from adapter.targeted_state import compact_state


@dataclass(frozen=True)
class Preflight:
    safe: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    context: dict[str, Any]


def run_preflight(root: Path) -> Preflight:
    blockers = []
    warnings = []

    adapter = ControllerAdapter(root)
    if not adapter.entrypoint.exists():
        blockers.append("CONTROL_CENTER_ENTRYPOINT_MISSING")
        return Preflight(False, tuple(blockers), tuple(warnings), {})

    try:
        context = compact_state(root)
    except Exception as exc:
        blockers.append(f"STATE_READ_FAILURE:{type(exc).__name__}")
        return Preflight(False, tuple(blockers), tuple(warnings), {})

    plan_current = context["plan_current"]["gate"]
    current_gate = context["current_gate"]

    if not plan_current:
        blockers.append("NO_CURRENT_PLAN_GATE")
    elif plan_current != current_gate:
        blockers.append("EXECUTION_PLAN_CURRENT_GATE_MISMATCH")

    if context["criteria"]["pending"] and context["gate_status"] in {"VALIDATED", "READY_FOR_APPROVAL"}:
        warnings.append("Gate has pending criteria despite validation-like status; inspect controller semantics.")

    return Preflight(not blockers, tuple(blockers), tuple(warnings), context)
