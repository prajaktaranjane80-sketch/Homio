from __future__ import annotations

"""
HOMIO Autonomous Work Cycle.

Purpose
-------
Turn the authoritative HOMIO mission position into a deterministic,
targeted, agent-ready work cycle.

This module does NOT:
- become a second controller,
- change Control Center state,
- invent roadmap tasks,
- execute repository mutations,
- bypass ACRL,
- bypass AUTONOMY_ENGINE safety boundaries.

It prepares the smallest useful work package for the existing
AUTONOMY_ENGINE/ACRL stack.

Flow
----
HOMIO_AUTONOMOUS_MASTER_PLAN.json
        +
REOS_CONTROL_CENTER/data/state.json
        |
        v
AutonomousMissionRuntime
        |
        v
MissionCycle
        |
        +--> targeted evidence targets
        +--> dependency inspection targets
        +--> test discovery targets
        +--> architecture checks
        +--> risk / approval boundary
        +--> agent execution context
"""

from dataclasses import asdict, dataclass
from typing import Any, Literal
from uuid import uuid4

from orchestration.agent_runtime import AgentRuntime, AgentRuntimeContext

from .autonomous_mission_runtime import (
    AutonomousMissionRuntime,
    MissionDecision,
)


CycleStatus = Literal[
    "READY",
    "BLOCKED",
]


@dataclass(frozen=True, slots=True)
class EvidenceTarget:
    """
    One targeted information request.

    A target describes WHAT must be inspected.
    It does not perform the inspection.
    """

    target_id: str
    category: str
    purpose: str
    priority: int
    required: bool
    max_items: int


@dataclass(frozen=True, slots=True)
class MissionCycle:
    """
    Deterministic work package for one HOMIO autonomous cycle.
    """

    cycle_id: str
    status: CycleStatus
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
                asdict(item)
                for item in self.evidence_targets
            ],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "agent_context": dict(self.agent_context),
        }


class MissionCycleEngine:
    """
    Convert one authoritative mission decision into an execution-ready
    inspection cycle.
    """

    def __init__(
        self,
        runtime: AutonomousMissionRuntime | None = None,
    ) -> None:
        self.runtime = runtime or AutonomousMissionRuntime()

    @staticmethod
    def _evidence_targets(
        decision: MissionDecision,
    ) -> tuple[EvidenceTarget, ...]:
        position = decision.position

        if not position.current_subtask:
            return ()

        return (
            EvidenceTarget(
                target_id="canonical-state",
                category="STATE",
                purpose=(
                    "Verify canonical execution position, state integrity "
                    "and current authority before any work."
                ),
                priority=100,
                required=True,
                max_items=1,
            ),
            EvidenceTarget(
                target_id="current-gate",
                category="GATE",
                purpose=(
                    "Inspect current gate definition, subtasks and "
                    "acceptance criteria."
                ),
                priority=95,
                required=True,
                max_items=1,
            ),
            EvidenceTarget(
                target_id="current-subtask",
                category="IMPLEMENTATION",
                purpose=(
                    "Locate the smallest relevant implementation surface "
                    "for the authoritative current subtask."
                ),
                priority=90,
                required=True,
                max_items=12,
            ),
            EvidenceTarget(
                target_id="dependency-impact",
                category="DEPENDENCY",
                purpose=(
                    "Resolve direct dependencies, owners and downstream "
                    "impact before changing code."
                ),
                priority=85,
                required=True,
                max_items=20,
            ),
            EvidenceTarget(
                target_id="architecture-contract",
                category="ARCHITECTURE",
                purpose=(
                    "Confirm frozen HOMIO architecture, contracts and "
                    "source-of-truth boundaries relevant to the subtask."
                ),
                priority=80,
                required=True,
                max_items=10,
            ),
            EvidenceTarget(
                target_id="test-surface",
                category="TEST",
                purpose=(
                    "Identify the smallest targeted tests plus required "
                    "regression surface for the change."
                ),
                priority=75,
                required=True,
                max_items=20,
            ),
            EvidenceTarget(
                target_id="risk-boundary",
                category="GOVERNANCE",
                purpose=(
                    "Determine whether the proposed work crosses security, "
                    "financial, legal, privacy, destructive or approval boundaries."
                ),
                priority=70,
                required=True,
                max_items=10,
            ),
            EvidenceTarget(
                target_id="change-impact",
                category="IMPACT",
                purpose=(
                    "Estimate affected modules and detect duplicate or "
                    "overlapping responsibility before implementation."
                ),
                priority=65,
                required=True,
                max_items=20,
            ),
        )

    @staticmethod
    def _agent_context(
        decision: MissionDecision,
        cycle_id: str,
    ) -> dict[str, Any]:
        position = decision.position

        return {
            "cycle_id": cycle_id,
            "mode": position.mode,
            "current_gate": position.current_gate,
            "current_task": position.current_task,
            "current_subtask": position.current_subtask,
            "next_gate": position.next_gate,
            "criteria_total": position.criteria_total,
            "criteria_verified": position.criteria_verified,
            "criteria_pending": position.criteria_pending,
            "operating_rules": [
                "discover_before_modify",
                "verify_before_assume",
                "diagnose_before_repair",
                "never_bypass_control_center",
                "never_modify_state_json_directly",
                "never_dump_full_files_unnecessarily",
                "record_machine_verifiable_evidence",
                "stop_on_ambiguous_authority",
            ],
            "execution_budget": {
                "max_repository_targets": 20,
                "max_file_previews": 12,
                "max_context_chars": 24000,
                "never_dump_full_file": True,
            },
        }

    def prepare(
        self,
        mode: str = "HOMIO_BUILDER",
    ) -> MissionCycle:
        decision = self.runtime.decide(mode=mode)  # type: ignore[arg-type]
        cycle_id = f"HOMIO-CYCLE-{uuid4()}"

        if decision.status == "BLOCKED":
            return MissionCycle(
                cycle_id=cycle_id,
                status="BLOCKED",
                mode=mode,
                gate=decision.position.current_gate,
                task=decision.position.current_task,
                subtask=decision.position.current_subtask,
                risk="UNKNOWN",
                mutation_allowed=False,
                approval_required=True,
                evidence_targets=(),
                blockers=decision.blockers,
                warnings=decision.warnings,
                agent_context={
                    "cycle_id": cycle_id,
                    "reason": "MISSION_RUNTIME_BLOCKED",
                },
            )

        evidence_targets = self._evidence_targets(decision)

        return MissionCycle(
            cycle_id=cycle_id,
            status="READY",
            mode=mode,
            gate=decision.position.current_gate,
            task=decision.position.current_task,
            subtask=decision.position.current_subtask,
            risk="LOW",
            mutation_allowed=False,
            approval_required=False,
            evidence_targets=evidence_targets,
            blockers=decision.blockers,
            warnings=decision.warnings,
            agent_context=self._agent_context(
                decision,
                cycle_id,
            ),
        )

    def create_agent_runtime(
        self,
        cycle: MissionCycle,
        *,
        agent_id: str = "homio-autonomous-engineer",
    ) -> AgentRuntime:
        """
        Create an existing AgentRuntime around the prepared mission cycle.

        This does not execute the agent.
        """

        if cycle.status != "READY":
            raise RuntimeError(
                "Cannot create an agent runtime for a blocked mission cycle."
            )

        if not cycle.subtask:
            raise RuntimeError(
                "Cannot create an agent runtime without a current subtask."
            )

        context = AgentRuntimeContext(
            run_id=cycle.cycle_id,
            agent_id=agent_id,
            task_id=cycle.subtask,
            metadata=cycle.agent_context,
        )

        return AgentRuntime(context)

    def build_cycle(
        self,
        mode: str = "HOMIO_BUILDER",
        *,
        agent_id: str = "homio-autonomous-engineer",
    ) -> dict[str, Any]:
        """
        Build a complete machine-readable autonomous work cycle.
        """

        cycle = self.prepare(mode=mode)

        result = cycle.to_dict()

        if cycle.status == "READY":
            agent = self.create_agent_runtime(
                cycle,
                agent_id=agent_id,
            )

            result["agent_runtime"] = {
                "status": agent.status,
                "run_id": agent.context.run_id,
                "agent_id": agent.context.agent_id,
                "task_id": agent.context.task_id,
            }

        return result
