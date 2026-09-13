from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from autonomous_mission_runtime import AutonomousMissionRuntime


@dataclass(frozen=True, slots=True)
class EvidenceTarget:
    target_id: str
    category: str
    purpose: str
    priority: int
    required: bool
    max_items: int


@dataclass(frozen=True, slots=True)
class MissionCycle:
    cycle_id: str
    status: str
    mode: str
    gate: str | None
    task: str | None
    subtask: str | None
    risk: str
    mutation_allowed: bool
    approval_required: bool
    evidence_targets: tuple[EvidenceTarget, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    agent_context: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "status": self.status,
            "mode": self.mode,
            "gate": self.gate,
            "task": self.task,
            "subtask": self.subtask,
            "risk": self.risk,
            "mutation_allowed": self.mutation_allowed,
            "approval_required": self.approval_required,
            "evidence_targets": [
                asdict(item) for item in self.evidence_targets
            ],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "agent_context": dict(self.agent_context),
        }


class MissionCycleEngine:
    """Build one bounded autonomous HOMIO work cycle."""

    def __init__(self, runtime: AutonomousMissionRuntime | None = None) -> None:
        self.runtime = runtime or AutonomousMissionRuntime()

    @staticmethod
    def _targets() -> tuple[EvidenceTarget, ...]:
        return (
            EvidenceTarget(
                "canonical-state",
                "STATE",
                "Verify canonical project state and integrity.",
                100,
                True,
                1,
            ),
            EvidenceTarget(
                "current-gate",
                "GATE",
                "Inspect authoritative gate and acceptance criteria.",
                95,
                True,
                1,
            ),
            EvidenceTarget(
                "current-subtask",
                "IMPLEMENTATION",
                "Locate the smallest relevant implementation surface.",
                90,
                True,
                12,
            ),
            EvidenceTarget(
                "dependencies",
                "DEPENDENCY",
                "Resolve direct dependencies and ownership.",
                85,
                True,
                20,
            ),
            EvidenceTarget(
                "architecture",
                "ARCHITECTURE",
                "Confirm frozen architecture and contracts.",
                80,
                True,
                10,
            ),
            EvidenceTarget(
                "tests",
                "TEST",
                "Select targeted tests and regression surface.",
                75,
                True,
                20,
            ),
            EvidenceTarget(
                "risk",
                "GOVERNANCE",
                "Determine risk and approval boundary.",
                70,
                True,
                10,
            ),
            EvidenceTarget(
                "impact",
                "IMPACT",
                "Detect blast-radius and duplicate responsibility.",
                65,
                True,
                20,
            ),
        )

    def prepare(self, mode: str = "HOMIO_BUILDER") -> MissionCycle:
        from uuid import uuid4

        decision = self.runtime.decide(mode=mode)
        cycle_id = f"HOMIO-CYCLE-{uuid4()}"

        if decision.status == "BLOCKED":
            return MissionCycle(
                cycle_id,
                "BLOCKED",
                mode,
                decision.position.current_gate,
                decision.position.current_task,
                decision.position.current_subtask,
                "UNKNOWN",
                False,
                True,
                (),
                decision.blockers,
                decision.warnings,
                {"cycle_id": cycle_id},
            )

        context = {
            "cycle_id": cycle_id,
            "gate": decision.position.current_gate,
            "task": decision.position.current_task,
            "subtask": decision.position.current_subtask,
            "next_gate": decision.position.next_gate,
            "rules": [
                "discover_before_modify",
                "verify_before_assume",
                "diagnose_before_repair",
                "never_bypass_control_center",
                "never_modify_state_json_directly",
                "never_dump_full_files",
                "record_machine_verifiable_evidence",
            ],
        }

        return MissionCycle(
            cycle_id,
            "READY",
            mode,
            decision.position.current_gate,
            decision.position.current_task,
            decision.position.current_subtask,
            "LOW",
            False,
            False,
            self._targets(),
            (),
            decision.warnings,
            context,
        )
