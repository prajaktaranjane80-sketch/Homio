from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class LoopStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    EXHAUSTED = "EXHAUSTED"
    FAILED = "FAILED"


class LoopDecision(str, Enum):
    STARTED = "STARTED"
    CONTINUE = "CONTINUE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    NO_PROGRESS = "NO_PROGRESS"
    CHECKPOINT_REQUIRED = "CHECKPOINT_REQUIRED"
    BLOCKED = "BLOCKED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class LoopIteration:
    iteration: int
    iteration_fingerprint: str

    progress_fingerprint: str
    checkpoint_fingerprint: str
    continuity_fingerprint: str

    work_consumed: int
    token_consumed: int
    context_consumed: int

    retry_count: int

    completed: bool
    blocked: bool

    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "iteration_fingerprint": self.iteration_fingerprint,
            "progress_fingerprint": self.progress_fingerprint,
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
            "continuity_fingerprint": self.continuity_fingerprint,
            "work_consumed": self.work_consumed,
            "token_consumed": self.token_consumed,
            "context_consumed": self.context_consumed,
            "retry_count": self.retry_count,
            "completed": self.completed,
            "blocked": self.blocked,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class ExecutionLoop:
    schema_version: str
    loop_version: str

    loop_id: str
    status: LoopStatus

    execution_intent: str

    checkpoint_id: str
    checkpoint_fingerprint: str

    continuity_recovery_id: str
    continuity_fingerprint: str

    evidence_resolution_id: str
    evidence_fingerprint: str

    max_iterations: int
    max_retries_per_iteration: int

    current_iteration: int

    total_work_budget: int
    total_token_budget: int
    total_context_budget: int

    work_consumed: int
    token_consumed: int
    context_consumed: int

    no_progress_limit: int
    no_progress_count: int

    iterations: tuple[
        LoopIteration,
        ...
    ]

    terminal_reason: str | None

    loop_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "loop_version": self.loop_version,
            "loop_id": self.loop_id,
            "status": self.status.value,
            "execution_intent": self.execution_intent,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
            "continuity_recovery_id": self.continuity_recovery_id,
            "continuity_fingerprint": self.continuity_fingerprint,
            "evidence_resolution_id": self.evidence_resolution_id,
            "evidence_fingerprint": self.evidence_fingerprint,
            "max_iterations": self.max_iterations,
            "max_retries_per_iteration": self.max_retries_per_iteration,
            "current_iteration": self.current_iteration,
            "total_work_budget": self.total_work_budget,
            "total_token_budget": self.total_token_budget,
            "total_context_budget": self.total_context_budget,
            "work_consumed": self.work_consumed,
            "token_consumed": self.token_consumed,
            "context_consumed": self.context_consumed,
            "no_progress_limit": self.no_progress_limit,
            "no_progress_count": self.no_progress_count,
            "iterations": [
                item.to_dict()
                for item in self.iterations
            ],
            "terminal_reason": self.terminal_reason,
            "loop_fingerprint": self.loop_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class LoopRequest:
    loop_id: str
    execution_intent: str

    checkpoint_id: str
    checkpoint_fingerprint: str

    continuity_recovery_id: str
    continuity_fingerprint: str

    evidence_resolution_id: str
    evidence_fingerprint: str

    max_iterations: int
    max_retries_per_iteration: int
    no_progress_limit: int

    total_work_budget: int
    total_token_budget: int
    total_context_budget: int

    request_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "execution_intent": self.execution_intent,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
            "continuity_recovery_id": self.continuity_recovery_id,
            "continuity_fingerprint": self.continuity_fingerprint,
            "evidence_resolution_id": self.evidence_resolution_id,
            "evidence_fingerprint": self.evidence_fingerprint,
            "max_iterations": self.max_iterations,
            "max_retries_per_iteration": self.max_retries_per_iteration,
            "no_progress_limit": self.no_progress_limit,
            "total_work_budget": self.total_work_budget,
            "total_token_budget": self.total_token_budget,
            "total_context_budget": self.total_context_budget,
            "request_fingerprint": self.request_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class LoopResult:
    schema_version: str

    decision: LoopDecision
    reason: str

    loop: ExecutionLoop | None

    request_fingerprint: str
    result_fingerprint: str

    next_layer: str | None

    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason,
            "loop": (
                self.loop.to_dict()
                if self.loop
                else None
            ),
            "request_fingerprint": self.request_fingerprint,
            "result_fingerprint": self.result_fingerprint,
            "next_layer": self.next_layer,
            "explanation": self.explanation,
        }
