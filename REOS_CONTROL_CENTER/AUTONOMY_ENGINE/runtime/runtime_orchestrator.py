from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autonomous_mission_runtime import (
    AutonomousMissionRuntime,
)
from dependency_runtime import DependencyRuntime
from evidence_runtime import EvidenceRuntime
from repository_runtime import RepositoryRuntime
from risk_runtime import RiskRuntime
from test_runtime import TestRuntime
from work_context import ContextItem, WorkContext


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    status: str
    mission: dict[str, Any]
    context: dict[str, Any]
    repository: dict[str, Any]
    tests: list[dict[str, Any]]
    risk: dict[str, Any]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mission": dict(self.mission),
            "context": dict(self.context),
            "repository": dict(self.repository),
            "tests": list(self.tests),
            "risk": dict(self.risk),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


class RuntimeOrchestrator:
    """Compose runtime capabilities into one bounded observation cycle."""

    def __init__(
        self,
        root: Path,
        *,
        mission_runtime: AutonomousMissionRuntime | None = None,
    ) -> None:
        self.root = Path(root).resolve()

        self.mission = (
            mission_runtime
            or AutonomousMissionRuntime(
                root=self.root,
                master_plan_path=(
                    self.root
                    / "HOMIO_AUTONOMOUS_MASTER_PLAN.json"
                ),
                state_path=(
                    self.root
                    / "data"
                    / "state.json"
                ),
            )
        )

        self.context = WorkContext()
        self.repository = RepositoryRuntime(
            self.root
        )
        self.dependencies = DependencyRuntime(
            self.root
        )
        self.tests = TestRuntime(
            self.root
        )
        self.risk = RiskRuntime()
        self.evidence = EvidenceRuntime(
            self.root
            / "runtime"
            / "evidence.jsonl"
        )

    def prepare(
        self,
        *,
        mode: str = "HOMIO_BUILDER",
    ) -> RuntimeObservation:
        decision = self.mission.decide(
            mode=mode
        )

        if decision.status == "BLOCKED":
            return RuntimeObservation(
                "BLOCKED",
                decision.position.__dict__
                if hasattr(
                    decision.position,
                    "__dict__",
                )
                else {
                    "mode": decision.position.mode,
                    "current_gate": decision.position.current_gate,
                    "current_task": decision.position.current_task,
                    "current_subtask": decision.position.current_subtask,
                },
                {},
                {},
                [],
                {},
                decision.blockers,
                decision.warnings,
            )

        keywords = [
            item
            for item in (
                decision.position.current_gate,
                decision.position.current_task,
                decision.position.current_subtask,
            )
            if item
        ]

        findings = self.repository.find_paths(
            keywords
        )

        tests = self.tests.discover(
            keywords
        )

        description = " ".join(
            keywords
        )

        risk = self.risk.classify(
            description
        )

        context = self.context.compile(
            [
                ContextItem(
                    "MISSION",
                    "current_gate",
                    decision.position.current_gate,
                    100,
                ),
                ContextItem(
                    "MISSION",
                    "current_task",
                    decision.position.current_task,
                    99,
                ),
                ContextItem(
                    "MISSION",
                    "current_subtask",
                    decision.position.current_subtask,
                    98,
                ),
                ContextItem(
                    "REPOSITORY",
                    "candidate_paths",
                    [x.path for x in findings],
                    90,
                ),
                ContextItem(
                    "TEST",
                    "candidate_tests",
                    [x.path for x in tests],
                    85,
                ),
            ]
        )

        self.evidence.append(
            self.evidence.create(
                evidence_id=(
                    "MISSION:"
                    + str(
                        decision.position.current_subtask
                    )
                ),
                kind="MISSION_POSITION",
                source="RuntimeOrchestrator",
                claim=(
                    "Authoritative current subtask resolved"
                ),
                metadata={
                    "gate": decision.position.current_gate,
                    "task": decision.position.current_task,
                    "subtask": decision.position.current_subtask,
                    "mode": mode,
                },
            )
        )

        return RuntimeObservation(
            "READY",
            {
                "mode": decision.position.mode,
                "current_gate": decision.position.current_gate,
                "current_task": decision.position.current_task,
                "current_subtask": decision.position.current_subtask,
                "next_gate": decision.position.next_gate,
                "criteria_total": decision.position.criteria_total,
                "criteria_verified": decision.position.criteria_verified,
                "criteria_pending": decision.position.criteria_pending,
            },
            context,
            {
                "branch": self.repository.branch(),
                "head": self.repository.head(),
                "worktree_clean": self.repository.worktree_clean(),
                "findings": [
                    {
                        "path": x.path,
                        "reason": x.reason,
                        "category": x.category,
                    }
                    for x in findings
                ],
            },
            [
                {
                    "path": x.path,
                    "reason": x.reason,
                    "confidence": x.confidence,
                }
                for x in tests
            ],
            {
                "level": risk.level,
                "mutation_allowed": risk.mutation_allowed,
                "approval_required": risk.approval_required,
                "blockers": list(risk.blockers),
                "reasons": list(risk.reasons),
            },
            decision.blockers,
            decision.warnings,
        )
