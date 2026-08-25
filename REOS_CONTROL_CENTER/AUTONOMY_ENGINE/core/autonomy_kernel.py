
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.integrity import IntegrityEngine
from core.models import ContextSnapshot
from execution.guard import ExecutionGuard
from memory.context_store import ContextStore
from memory.evidence_ledger import EvidenceLedger


class AutonomyKernel:
    """
    Main orchestration layer.

    The kernel intentionally stops at proposal/verification boundaries until
    an explicit Control Center adapter is installed.
    """

    def __init__(self, engine_root: Path) -> None:
        self.engine_root = engine_root
        self.control_root = engine_root.parent
        self.state_path = self.control_root / "data" / "state.json"
        runtime = engine_root / "runtime"
        self.context_store = ContextStore(runtime / "context.json")
        self.evidence = EvidenceLedger(runtime / "evidence.jsonl")
        self.integrity = IntegrityEngine(self.state_path)
        self.guard = ExecutionGuard()

    def _state(self) -> dict[str, Any]:
        return self.integrity.load_state()

    def context(self) -> ContextSnapshot:
        state = self._state()
        execution = state.get("execution", {})
        current_gate = execution.get("current_gate")
        current_task = execution.get("current_task")
        current_subtask = execution.get("current_subtask")
        seq = state.get("execution_plan", {}).get("authoritative_sequence", [])
        current_entries = [
            x for x in seq
            if isinstance(x, dict) and x.get("status") == "CURRENT"
        ]
        plan_current = current_entries[0].get("gate") if len(current_entries) == 1 else None
        next_gate = None
        if plan_current:
            for i, entry in enumerate(seq):
                if isinstance(entry, dict) and entry.get("gate") == plan_current:
                    if i + 1 < len(seq) and isinstance(seq[i + 1], dict):
                        next_gate = seq[i + 1].get("gate")
                    break

        gate_plan = state.get("gate_plans", {}).get(current_gate, {})
        subtasks = gate_plan.get("subtasks", gate_plan.get("subtask_state", []))
        criteria = gate_plan.get("criteria_state", gate_plan.get("acceptance_criteria", []))
        subtasks = subtasks if isinstance(subtasks, list) else []
        criteria = criteria if isinstance(criteria, list) else []

        verified = sum(1 for x in criteria if isinstance(x, dict) and x.get("status") == "VERIFIED")
        pending = sum(1 for x in criteria if isinstance(x, dict) and x.get("status") in {"PENDING", "UNVERIFIED"})

        blockers = []
        if len(current_entries) != 1:
            blockers.append("CURRENT_GATE_NOT_UNIQUE")

        # Conservative semantic note:
        # We do not compare architecture registry state to execution plan state
        # here because their lifecycle semantics must be proven by controller rules.
        warnings = []
        if state.get("architecture"):
            warnings.append("Architecture records exist; semantic lifecycle comparison is intentionally conservative.")

        snapshot = ContextSnapshot(
            generated_at=datetime.now(timezone.utc).isoformat(),
            current_gate=current_gate,
            current_task=current_task,
            current_subtask=current_subtask,
            gate_status=gate_plan.get("status") if isinstance(gate_plan, dict) else None,
            criteria_total=len(criteria),
            criteria_verified=verified,
            criteria_pending=pending,
            plan_current_gate=plan_current,
            next_gate=next_gate,
            state_integrity="UNKNOWN",
            blockers=blockers,
            warnings=warnings,
        )
        self.context_store.save(snapshot.__dict__)
        return snapshot
