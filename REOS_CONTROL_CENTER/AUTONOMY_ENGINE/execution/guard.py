
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

class ExecutionGuard:
    """
    General fail-closed gate for the autonomous layer.

    It does not assume a controller command is legal merely because the
    agent requested it.
    """

    def evaluate(
        self,
        *,
        integrity_ok: bool,
        semantic_status: str,
        architecture_locked: bool,
        required_evidence_ok: bool,
        mutation_requested: bool,
    ) -> GuardDecision:
        blockers: list[str] = []
        warnings: list[str] = []

        if not integrity_ok:
            blockers.append("STATE_INTEGRITY_FAILURE")

        if semantic_status in {"CONTRADICTION", "UNKNOWN"}:
            blockers.append(f"SEMANTIC_STATUS_{semantic_status}")

        if mutation_requested and not architecture_locked:
            blockers.append("ARCHITECTURE_LOCK_NOT_PROVEN")

        if mutation_requested and not required_evidence_ok:
            blockers.append("REQUIRED_EVIDENCE_NOT_PROVEN")

        return GuardDecision(
            allowed=not blockers,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )
