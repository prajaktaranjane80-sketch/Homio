
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from integration.preflight import run_preflight


@dataclass(frozen=True)
class SafeAction:
    status: str
    action: str
    reason: str
    context: dict[str, Any]


def next_safe_action(root: Path) -> SafeAction:
    pf = run_preflight(root)

    if not pf.safe:
        return SafeAction(
            "BLOCKED",
            "STOP_AND_DIAGNOSE",
            "; ".join(pf.blockers),
            pf.context,
        )

    c = pf.context

    if c["criteria"]["pending"]:
        return SafeAction(
            "READY",
            "VERIFY_REMAINING_CRITERIA",
            "Current gate has unverified acceptance criteria; do not approve yet.",
            c,
        )

    if c["subtasks"]["current"]:
        return SafeAction(
            "READY",
            "CONTINUE_CURRENT_SUBTASK",
            f"Current subtask: {c['subtasks']['current'][0]}",
            c,
        )

    return SafeAction(
        "REVIEW_REQUIRED",
        "INSPECT_CONTROLLER_GATE_STATUS",
        "No single safe mutation was inferred; inspect controller semantics first.",
        c,
    )
