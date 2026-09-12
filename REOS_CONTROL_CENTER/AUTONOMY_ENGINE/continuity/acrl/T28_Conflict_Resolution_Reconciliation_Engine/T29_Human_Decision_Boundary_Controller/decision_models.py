from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DecisionType(str, Enum):
    NONE = "NONE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ACKNOWLEDGE = "ACKNOWLEDGE"


class BoundaryDecision(str, Enum):
    AUTONOMY_ALLOWED = "AUTONOMY_ALLOWED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    HUMAN_EXPIRED = "HUMAN_EXPIRED"
    INVALID_DECISION = "INVALID_DECISION"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    FAIL_CLOSED = "FAIL_CLOSED"


class DecisionStatus(str, Enum):
    CREATED = "CREATED"
    WAITING = "WAITING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DecisionPolicy:
    policy_version: str = "1.0"
    require_human_for_unresolved: bool = True
    require_human_for_critical: bool = True
    allow_expiration: bool = True
    max_decision_age: int = 3600


@dataclass(frozen=True)
class DecisionRequest:
    decision_id: str
    reconciliation_fingerprint: str
    reconciliation_decision: str
    continuity_fingerprint: str
    evidence_fingerprint: str
    policy: DecisionPolicy
    boundary_reason: str
    requested_decision_type: DecisionType = DecisionType.APPROVE


@dataclass(frozen=True)
class HumanDecision:
    decision_id: str
    decision_type: DecisionType
    decided_by: str
    decision_timestamp: int
    rationale: str
    evidence_ids: tuple[str, ...] = ()
    nonce: str = ""


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    status: DecisionStatus
    boundary_decision: BoundaryDecision
    decision_type: DecisionType
    decided_by: str | None
    rationale: str
    fingerprint: str


@dataclass(frozen=True)
class DecisionResult:
    record: DecisionRecord
    audit: dict[str, Any] = field(default_factory=dict)
