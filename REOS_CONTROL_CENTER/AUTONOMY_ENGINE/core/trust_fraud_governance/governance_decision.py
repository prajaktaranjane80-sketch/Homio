"""CORE-007 — Governance Decision & Escalation Boundary.

ARCH-017 bounded decision interpretation authority.

This module consumes:
- CORE-007 GovernanceEvaluation.

This module produces:
- an immutable GovernanceDecision describing the governance disposition.

This module does NOT:
- authorize users or services,
- grant permissions,
- deny API access,
- execute mutations,
- execute payments,
- own approval persistence,
- own Control Center state,
- own ACRL state,
- publish transport events,
- replace CORE-001 authorization,
- replace CORE-002 event infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from .governance_engine import (
    GovernanceEvaluation,
    GovernanceEvaluationConflictError,
)
from .governance_policy import (
    GovernanceActionClass,
    GovernanceDisposition,
)


GOVERNANCE_DECISION_SCHEMA_VERSION = 1
GOVERNANCE_DECISION_ENGINE_VERSION = "1.0"


class GovernanceDecisionError(ValueError):
    """Base governance decision error."""


class GovernanceDecisionValidationError(
    GovernanceDecisionError
):
    """Invalid decision contract."""


class GovernanceDecisionConflictError(
    GovernanceDecisionError
):
    """Conflicting decision identity."""


class GovernanceDecisionType(str, Enum):
    CONTINUE = "CONTINUE"
    REVIEW = "REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"


class GovernanceAuthorityClass(str, Enum):
    STANDARD_REVIEW = "STANDARD_REVIEW"
    SENIOR_REVIEW = "SENIOR_REVIEW"
    COMPLIANCE = "COMPLIANCE"
    SECURITY = "SECURITY"
    FINANCIAL = "FINANCIAL"
    EXECUTIVE = "EXECUTIVE"


class GovernanceEscalationLevel(str, Enum):
    NONE = "NONE"
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceDecisionValidationError(
            f"{field_name} must be non-empty text."
        )

    return value.strip()


def _utc(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise GovernanceDecisionValidationError(
            f"{field_name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise GovernanceDecisionValidationError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        return _utc(value, "datetime").isoformat()

    if isinstance(value, dict):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(
                value,
                key=lambda item: str(item),
            )
        }

    if isinstance(value, (tuple, list)):
        return [
            _canonicalize(item)
            for item in value
        ]

    if (
        isinstance(
            value,
            (str, int, float, bool),
        )
        or value is None
    ):
        return value

    raise GovernanceDecisionValidationError(
        "Unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def _fingerprint(value: Any) -> str:
    payload = json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    """Immutable governance disposition.

    A GovernanceDecision is descriptive/control-plane output.
    It is deliberately NOT an authorization verdict.
    """

    decision_id: UUID

    tenant_id: str
    subject_id: str
    correlation_id: str

    policy_id: str
    policy_version: str
    policy_fingerprint: str

    source_evaluation_fingerprint: str

    decision_type: GovernanceDecisionType
    action_class: GovernanceActionClass

    approval_required: bool
    required_authority: GovernanceAuthorityClass | None

    escalation_level: GovernanceEscalationLevel

    matched_rule_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    evidence_references: tuple[str, ...]

    decided_at: datetime
    schema_version: int
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(self.tenant_id, "tenant_id"),
        )
        object.__setattr__(
            self,
            "subject_id",
            _text(self.subject_id, "subject_id"),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _text(
                self.correlation_id,
                "correlation_id",
            ),
        )
        object.__setattr__(
            self,
            "policy_id",
            _text(
                self.policy_id,
                "policy_id",
            ),
        )
        object.__setattr__(
            self,
            "policy_version",
            _text(
                self.policy_version,
                "policy_version",
            ),
        )
        object.__setattr__(
            self,
            "policy_fingerprint",
            _text(
                self.policy_fingerprint,
                "policy_fingerprint",
            ),
        )
        object.__setattr__(
            self,
            "source_evaluation_fingerprint",
            _text(
                self.source_evaluation_fingerprint,
                "source_evaluation_fingerprint",
            ),
        )

        if not isinstance(
            self.decision_type,
            GovernanceDecisionType,
        ):
            raise GovernanceDecisionValidationError(
                "decision_type must be GovernanceDecisionType."
            )

        if not isinstance(
            self.action_class,
            GovernanceActionClass,
        ):
            raise GovernanceDecisionValidationError(
                "action_class must be GovernanceActionClass."
            )

        if not isinstance(
            self.approval_required,
            bool,
        ):
            raise GovernanceDecisionValidationError(
                "approval_required must be boolean."
            )

        if (
            self.approval_required
            and self.required_authority is None
        ):
            raise GovernanceDecisionValidationError(
                "required_authority is required "
                "when approval_required is true."
            )

        if self.required_authority is not None:
            if not isinstance(
                self.required_authority,
                GovernanceAuthorityClass,
            ):
                raise GovernanceDecisionValidationError(
                    "required_authority must be "
                    "GovernanceAuthorityClass."
                )

        if not isinstance(
            self.escalation_level,
            GovernanceEscalationLevel,
        ):
            raise GovernanceDecisionValidationError(
                "escalation_level must be "
                "GovernanceEscalationLevel."
            )

        if not self.approval_required and (
            self.decision_type
            is GovernanceDecisionType.APPROVAL_REQUIRED
        ):
            raise GovernanceDecisionValidationError(
                "APPROVAL_REQUIRED decision must "
                "set approval_required=true."
            )

        if self.decision_type is (
            GovernanceDecisionType.ESCALATION_REQUIRED
        ):
            if (
                self.escalation_level
                is GovernanceEscalationLevel.NONE
            ):
                raise GovernanceDecisionValidationError(
                    "Escalation decision requires "
                    "a non-NONE escalation level."
                )

        if not isinstance(
            self.matched_rule_ids,
            tuple,
        ):
            raise GovernanceDecisionValidationError(
                "matched_rule_ids must be tuple."
            )

        if not isinstance(
            self.reasons,
            tuple,
        ):
            raise GovernanceDecisionValidationError(
                "reasons must be tuple."
            )

        if not isinstance(
            self.evidence_references,
            tuple,
        ):
            raise GovernanceDecisionValidationError(
                "evidence_references must be tuple."
            )

        if self.schema_version != (
            GOVERNANCE_DECISION_SCHEMA_VERSION
        ):
            raise GovernanceDecisionValidationError(
                "Unsupported governance decision schema."
            )

        object.__setattr__(
            self,
            "decided_at",
            _utc(
                self.decided_at,
                "decided_at",
            ),
        )

    @property
    def determinism_key(self) -> tuple[Any, ...]:
        return (
            self.tenant_id,
            self.subject_id,
            self.correlation_id,
            self.policy_id,
            self.policy_version,
            self.policy_fingerprint,
            self.source_evaluation_fingerprint,
            self.decision_type.value,
            self.action_class.value,
            self.approval_required,
            (
                self.required_authority.value
                if self.required_authority is not None
                else None
            ),
            self.escalation_level.value,
            self.matched_rule_ids,
            self.reasons,
            self.evidence_references,
        )

    def assert_compatible(
        self,
        other: "GovernanceDecision",
    ) -> None:
        if not isinstance(
            other,
            GovernanceDecision,
        ):
            raise GovernanceDecisionValidationError(
                "other must be GovernanceDecision."
            )

        if (
            self.determinism_key
            != other.determinism_key
        ):
            raise GovernanceDecisionConflictError(
                "Conflicting governance decisions."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": str(self.decision_id),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "correlation_id": self.correlation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_fingerprint": self.policy_fingerprint,
            "source_evaluation_fingerprint": (
                self.source_evaluation_fingerprint
            ),
            "decision_type": self.decision_type.value,
            "action_class": self.action_class.value,
            "approval_required": self.approval_required,
            "required_authority": (
                self.required_authority.value
                if self.required_authority is not None
                else None
            ),
            "escalation_level": (
                self.escalation_level.value
            ),
            "matched_rule_ids": list(
                self.matched_rule_ids
            ),
            "reasons": list(self.reasons),
            "evidence_references": list(
                self.evidence_references
            ),
            "decided_at": self.decided_at.isoformat(),
            "schema_version": self.schema_version,
            "fingerprint": self.fingerprint,
            "engine_version": (
                GOVERNANCE_DECISION_ENGINE_VERSION
            ),
        }


class GovernanceDecisionEngine:
    """Translate governance disposition into controlled decision output."""

    @staticmethod
    def from_evaluation(
        evaluation: GovernanceEvaluation,
        *,
        evidence_references: tuple[str, ...] = (),
        decided_at: datetime | None = None,
        decision_id: UUID | None = None,
    ) -> GovernanceDecision:
        if not isinstance(
            evaluation,
            GovernanceEvaluation,
        ):
            raise GovernanceDecisionValidationError(
                "evaluation must be GovernanceEvaluation."
            )

        disposition = evaluation.disposition

        if disposition is GovernanceDisposition.CONTINUE:
            decision_type = (
                GovernanceDecisionType.CONTINUE
            )
            approval_required = False
            authority = None
            escalation = GovernanceEscalationLevel.NONE

        elif disposition is GovernanceDisposition.REVIEW:
            decision_type = (
                GovernanceDecisionType.REVIEW
            )
            approval_required = False
            authority = (
                GovernanceAuthorityClass.STANDARD_REVIEW
            )
            escalation = (
                GovernanceEscalationLevel.REVIEW
            )

        elif disposition is (
            GovernanceDisposition.APPROVAL_REQUIRED
        ):
            decision_type = (
                GovernanceDecisionType.APPROVAL_REQUIRED
            )
            approval_required = True
            authority = (
                GovernanceAuthorityClass.SENIOR_REVIEW
            )
            escalation = (
                GovernanceEscalationLevel.HIGH
            )

        elif disposition is GovernanceDisposition.ESCALATE:
            decision_type = (
                GovernanceDecisionType.ESCALATION_REQUIRED
            )
            approval_required = True
            authority = (
                GovernanceAuthorityClass.EXECUTIVE
            )
            escalation = (
                GovernanceEscalationLevel.CRITICAL
            )

        else:
            raise GovernanceDecisionError(
                "Unsupported governance disposition."
            )

        timestamp = (
            decided_at
            if decided_at is not None
            else datetime.now(timezone.utc)
        )

        normalized_evidence = tuple(
            sorted(
                {
                    value.strip()
                    for value in evidence_references
                    if isinstance(value, str)
                    and value.strip()
                }
            )
        )

        material = {
            "tenant_id": evaluation.tenant_id,
            "subject_id": evaluation.subject_id,
            "correlation_id": evaluation.correlation_id,
            "policy_id": evaluation.policy_id,
            "policy_version": evaluation.policy_version,
            "policy_fingerprint": (
                evaluation.policy_fingerprint
            ),
            "source_evaluation_fingerprint": (
                evaluation.fingerprint
            ),
            "decision_type": decision_type,
            "action_class": evaluation.action_class,
            "approval_required": approval_required,
            "required_authority": authority,
            "escalation_level": escalation,
            "matched_rule_ids": (
                evaluation.matched_rule_ids
            ),
            "reasons": evaluation.reasons,
            "evidence_references": normalized_evidence,
            "decided_at": _utc(
                timestamp,
                "decided_at",
            ),
        }

        decision_fingerprint = _fingerprint(
            material
        )

        return GovernanceDecision(
            decision_id=(
                decision_id
                or uuid4()
            ),
            tenant_id=evaluation.tenant_id,
            subject_id=evaluation.subject_id,
            correlation_id=evaluation.correlation_id,
            policy_id=evaluation.policy_id,
            policy_version=evaluation.policy_version,
            policy_fingerprint=(
                evaluation.policy_fingerprint
            ),
            source_evaluation_fingerprint=(
                evaluation.fingerprint
            ),
            decision_type=decision_type,
            action_class=evaluation.action_class,
            approval_required=approval_required,
            required_authority=authority,
            escalation_level=escalation,
            matched_rule_ids=(
                evaluation.matched_rule_ids
            ),
            reasons=evaluation.reasons,
            evidence_references=(
                normalized_evidence
            ),
            decided_at=timestamp,
            schema_version=(
                GOVERNANCE_DECISION_SCHEMA_VERSION
            ),
            fingerprint=decision_fingerprint,
        )
