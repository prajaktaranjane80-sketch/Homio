from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class BudgetKind(str, Enum):
    CONTEXT = "CONTEXT"
    TOKEN = "TOKEN"
    WORK = "WORK"


class BudgetDecision(str, Enum):
    ALLOCATED = "ALLOCATED"
    READ_ONLY = "READ_ONLY"
    BLOCKED = "BLOCKED"
    EXHAUSTED = "EXHAUSTED"
    INVALID = "INVALID"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    FAIL_CLOSED = "FAIL_CLOSED"


class BudgetUnit(str, Enum):
    TOKENS = "TOKENS"
    ITEMS = "ITEMS"
    STEPS = "STEPS"
    BYTES = "BYTES"
    SECONDS = "SECONDS"


@dataclass(frozen=True, slots=True)
class ContextWindow:
    declared_capacity: int
    safety_reserve: int
    minimum_operational_capacity: int
    compression_reserve: int = 0

    @property
    def usable_capacity(self) -> int:
        return max(
            0,
            self.declared_capacity
            - self.safety_reserve
            - self.compression_reserve,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "declared_capacity": self.declared_capacity,
            "safety_reserve": self.safety_reserve,
            "minimum_operational_capacity": (
                self.minimum_operational_capacity
            ),
            "compression_reserve": (
                self.compression_reserve
            ),
            "usable_capacity": self.usable_capacity,
        }


@dataclass(frozen=True, slots=True)
class BudgetReservation:
    reservation_id: str
    request_id: str

    context_reserved: int
    token_reserved: int
    work_reserved: int

    context_consumed: int = 0
    token_consumed: int = 0
    work_consumed: int = 0

    released: bool = False

    def remaining(
        self,
    ) -> tuple[int, int, int]:
        return (
            max(
                0,
                self.context_reserved
                - self.context_consumed,
            ),
            max(
                0,
                self.token_reserved
                - self.token_consumed,
            ),
            max(
                0,
                self.work_reserved
                - self.work_consumed,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        context, token, work = self.remaining()

        return {
            "reservation_id": self.reservation_id,
            "request_id": self.request_id,
            "context_reserved": self.context_reserved,
            "token_reserved": self.token_reserved,
            "work_reserved": self.work_reserved,
            "context_consumed": self.context_consumed,
            "token_consumed": self.token_consumed,
            "work_consumed": self.work_consumed,
            "remaining_context": context,
            "remaining_token": token,
            "remaining_work": work,
            "released": self.released,
        }


@dataclass(frozen=True, slots=True)
class BudgetSnapshot:
    schema_version: str
    policy_version: str

    context_capacity: int
    context_reserved: int
    context_consumed: int

    token_capacity: int
    token_reserved: int
    token_consumed: int

    work_capacity: int
    work_reserved: int
    work_consumed: int

    context_remaining: int
    token_remaining: int
    work_remaining: int

    exhausted: bool

    snapshot_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "context_capacity": self.context_capacity,
            "context_reserved": self.context_reserved,
            "context_consumed": self.context_consumed,
            "token_capacity": self.token_capacity,
            "token_reserved": self.token_reserved,
            "token_consumed": self.token_consumed,
            "work_capacity": self.work_capacity,
            "work_reserved": self.work_reserved,
            "work_consumed": self.work_consumed,
            "context_remaining": self.context_remaining,
            "token_remaining": self.token_remaining,
            "work_remaining": self.work_remaining,
            "exhausted": self.exhausted,
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class BudgetRequest:
    request_id: str

    context_requested: int
    token_requested: int
    work_requested: int

    context_window: ContextWindow

    token_capacity: int
    work_capacity: int

    required_context_floor: int = 0
    required_token_floor: int = 0
    required_work_floor: int = 0

    source_resolution_id: str = ""
    recovery_id: str = ""

    allow_partial: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "context_requested": self.context_requested,
            "token_requested": self.token_requested,
            "work_requested": self.work_requested,
            "context_window": (
                self.context_window.to_dict()
            ),
            "token_capacity": self.token_capacity,
            "work_capacity": self.work_capacity,
            "required_context_floor": (
                self.required_context_floor
            ),
            "required_token_floor": (
                self.required_token_floor
            ),
            "required_work_floor": (
                self.required_work_floor
            ),
            "source_resolution_id": (
                self.source_resolution_id
            ),
            "recovery_id": self.recovery_id,
            "allow_partial": self.allow_partial,
        }


@dataclass(frozen=True, slots=True)
class BudgetResult:
    schema_version: str
    decision: BudgetDecision
    reason: str

    request_id: str

    snapshot: BudgetSnapshot

    reservation: BudgetReservation | None

    request_fingerprint: str
    result_fingerprint: str

    handoff_required: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason,
            "request_id": self.request_id,
            "snapshot": self.snapshot.to_dict(),
            "reservation": (
                self.reservation.to_dict()
                if self.reservation
                else None
            ),
            "request_fingerprint": (
                self.request_fingerprint
            ),
            "result_fingerprint": (
                self.result_fingerprint
            ),
            "handoff_required": (
                self.handoff_required
            ),
            "explanation": self.explanation,
        }
