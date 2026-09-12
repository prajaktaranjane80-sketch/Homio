from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkState(str, Enum):
    DECLARED = "DECLARED"
    WAITING = "WAITING"
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class DependencyState(str, Enum):
    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT"


class SchedulerStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class SchedulerDecision(str, Enum):
    SCHEDULED = "SCHEDULED"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    DEPENDENCY_CYCLE = "DEPENDENCY_CYCLE"
    NO_READY_WORK = "NO_READY_WORK"
    RESOURCE_BLOCKED = "RESOURCE_BLOCKED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class WorkUnit:
    work_id: str
    version: str
    description: str
    dependencies: tuple[str, ...]
    priority: int
    work_cost: int
    token_cost: int
    context_cost: int
    state: WorkState = WorkState.DECLARED
    retry_limit: int = 0
    idempotency_key: str = ""

    def to_dict(self) -> dict:
        return {
            "work_id": self.work_id,
            "version": self.version,
            "description": self.description,
            "dependencies": list(self.dependencies),
            "priority": self.priority,
            "work_cost": self.work_cost,
            "token_cost": self.token_cost,
            "context_cost": self.context_cost,
            "state": self.state.value,
            "retry_limit": self.retry_limit,
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True)
class SchedulerPolicy:
    max_parallel: int = 1
    allow_parallel: bool = False
    require_dependencies: bool = True
    require_budget: bool = True
    version: str = "1.0"

    def to_dict(self) -> dict:
        return {
            "max_parallel": self.max_parallel,
            "allow_parallel": self.allow_parallel,
            "require_dependencies": self.require_dependencies,
            "require_budget": self.require_budget,
            "version": self.version,
        }


@dataclass(frozen=True)
class SchedulerRequest:
    scheduler_id: str
    loop_id: str
    loop_fingerprint: str
    continuity_fingerprint: str
    evidence_fingerprint: str
    work_budget: int
    token_budget: int
    context_budget: int
    work_units: tuple[WorkUnit, ...]
    policy: SchedulerPolicy = SchedulerPolicy()

    def to_dict(self) -> dict:
        return {
            "scheduler_id": self.scheduler_id,
            "loop_id": self.loop_id,
            "loop_fingerprint": self.loop_fingerprint,
            "continuity_fingerprint": self.continuity_fingerprint,
            "evidence_fingerprint": self.evidence_fingerprint,
            "work_budget": self.work_budget,
            "token_budget": self.token_budget,
            "context_budget": self.context_budget,
            "work_units": [
                item.to_dict()
                for item in self.work_units
            ],
            "policy": self.policy.to_dict(),
        }


@dataclass(frozen=True)
class ScheduleSnapshot:
    scheduler_id: str
    loop_id: str
    status: SchedulerStatus
    ready_work: tuple[str, ...]
    waiting_work: tuple[str, ...]
    blocked_work: tuple[str, ...]
    completed_work: tuple[str, ...]
    failed_work: tuple[str, ...]
    ordered_work: tuple[str, ...]
    concurrency_groups: tuple[tuple[str, ...], ...]
    graph_fingerprint: str
    policy_fingerprint: str
    schedule_fingerprint: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "scheduler_id": self.scheduler_id,
            "loop_id": self.loop_id,
            "status": self.status.value,
            "ready_work": list(self.ready_work),
            "waiting_work": list(self.waiting_work),
            "blocked_work": list(self.blocked_work),
            "completed_work": list(self.completed_work),
            "failed_work": list(self.failed_work),
            "ordered_work": list(self.ordered_work),
            "concurrency_groups": [
                list(group)
                for group in self.concurrency_groups
            ],
            "graph_fingerprint": self.graph_fingerprint,
            "policy_fingerprint": self.policy_fingerprint,
            "schedule_fingerprint": self.schedule_fingerprint,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SchedulerResult:
    schema_version: str
    decision: SchedulerDecision
    snapshot: ScheduleSnapshot | None
    request_fingerprint: str
    result_fingerprint: str
    next_layer: str | None
    explanation: str

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "snapshot": (
                self.snapshot.to_dict()
                if self.snapshot
                else None
            ),
            "request_fingerprint": self.request_fingerprint,
            "result_fingerprint": self.result_fingerprint,
            "next_layer": self.next_layer,
            "explanation": self.explanation,
        }
