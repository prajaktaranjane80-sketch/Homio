from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
import hashlib
import json

from .governance_engine import GovernanceEvaluation
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
    """Invalid governance decision."""


class GovernanceDecisionConflictError(
    GovernanceDecisionError
):
    """Conflicting governance decision."""


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


class GovernanceReviewState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    COMPLETED = "COMPLETED"


class GovernanceEscalationState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceDecisionValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise GovernanceDecisionValidationError(
            "datetime must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return _utc(value).isoformat()

    if isinstance(value, dict):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [
            _canonical(item)
            for item in value
        ]

    return value


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        _canonical(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    """
    Immutable governance decision.

    This is NOT authorization.

    Explicitly models:
    - review state
    - escalation state
    - human review reference
    - decision evidence
    - override reference
    - override authorization
    - appeal/review reference
    - irreversible-action protection
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
    required_authority: (
        GovernanceAuthorityClass | None
    )

    escalation_level: GovernanceEscalationLevel

    matched_rule_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    evidence_references: tuple[str, ...]

    decided_at: datetime
    schema_version: int
    fingerprint: str

    review_state: GovernanceReviewState | None = None

    escalation_state: (
        GovernanceEscalationState | None
    ) = None

    human_review_reference: str | None = None

    decision_evidence: tuple[str, ...] = ()

    override_reference: str | None = None
    override_authorization: str | None = None

    appeal_review_reference: str | None = None

    irreversible_action_protected: bool = True

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "subject_id",
            "correlation_id",
            "policy_id",
            "policy_version",
            "policy_fingerprint",
            "source_evaluation_fingerprint",
        ):
            object.__setattr__(
                self,
                name,
                _text(
                    getattr(self, name),
                    name,
                ),
            )

        if not isinstance(
            self.decision_id,
            UUID,
        ):
            raise GovernanceDecisionValidationError(
                "decision_id must be UUID."
            )

        if not isinstance(
            self.decision_type,
            GovernanceDecisionType,
        ):
            raise GovernanceDecisionValidationError(
                "Invalid decision_type."
            )

        if not isinstance(
            self.action_class,
            GovernanceActionClass,
        ):
            raise GovernanceDecisionValidationError(
                "Invalid action_class."
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
                "required_authority required for approval."
            )

        if (
            self.required_authority is not None
            and not isinstance(
                self.required_authority,
                GovernanceAuthorityClass,
            )
        ):
            raise GovernanceDecisionValidationError(
                "Invalid required_authority."
            )

        if not isinstance(
            self.escalation_level,
            GovernanceEscalationLevel,
        ):
            raise GovernanceDecisionValidationError(
                "Invalid escalation_level."
            )

        if (
            self.decision_type
            is GovernanceDecisionType
            .APPROVAL_REQUIRED
            and not self.approval_required
        ):
            raise GovernanceDecisionValidationError(
                "APPROVAL_REQUIRED requires approval."
            )

        if (
            self.decision_type
            is GovernanceDecisionType
            .ESCALATION_REQUIRED
            and self.escalation_level
            is GovernanceEscalationLevel.NONE
        ):
            raise GovernanceDecisionValidationError(
                "Escalation decision requires level."
            )

        review_state = (
            self.review_state
            if self.review_state is not None
            else (
                GovernanceReviewState.NOT_REQUIRED
                if self.decision_type
                is GovernanceDecisionType.CONTINUE
                else GovernanceReviewState.PENDING
            )
        )

        if not isinstance(
            review_state,
            GovernanceReviewState,
        ):
            raise GovernanceDecisionValidationError(
                "Invalid review_state."
            )

        object.__setattr__(
            self,
            "review_state",
            review_state,
        )

        escalation_state = (
            self.escalation_state
            if self.escalation_state is not None
            else (
                GovernanceEscalationState.NOT_REQUIRED
                if self.escalation_level
                is GovernanceEscalationLevel.NONE
                else GovernanceEscalationState.OPEN
            )
        )

        if not isinstance(
            escalation_state,
            GovernanceEscalationState,
        ):
            raise GovernanceDecisionValidationError(
                "Invalid escalation_state."
            )

        object.__setattr__(
            self,
            "escalation_state",
            escalation_state,
        )

        object.__setattr__(
            self,
            "matched_rule_ids",
            tuple(
                _text(
                    item,
                    "matched_rule_id",
                )
                for item in self.matched_rule_ids
            ),
        )

        object.__setattr__(
            self,
            "reasons",
            tuple(
                _text(
                    item,
                    "reason",
                )
                for item in self.reasons
            ),
        )

        object.__setattr__(
            self,
            "evidence_references",
            tuple(
                _text(
                    item,
                    "evidence_reference",
                )
                for item in self.evidence_references
            ),
        )

        decision_evidence = (
            self.decision_evidence
            or self.evidence_references
        )

        object.__setattr__(
            self,
            "decision_evidence",
            tuple(
                _text(
                    item,
                    "decision_evidence",
                )
                for item in decision_evidence
            ),
        )

        if self.human_review_reference is None:
            if review_state is not (
                GovernanceReviewState.NOT_REQUIRED
            ):
                object.__setattr__(
                    self,
                    "human_review_reference",
                    (
                        f"human-review:"
                        f"{self.correlation_id}"
                    ),
                )
        else:
            object.__setattr__(
                self,
                "human_review_reference",
                _text(
                    self.human_review_reference,
                    "human_review_reference",
                ),
            )

        for name in (
            "override_reference",
            "override_authorization",
            "appeal_review_reference",
        ):
            value = getattr(self, name)

            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _text(
                        value,
                        name,
                    ),
                )

        if self.schema_version != (
            GOVERNANCE_DECISION_SCHEMA_VERSION
        ):
            raise GovernanceDecisionValidationError(
                "Unsupported decision schema."
            )

        object.__setattr__(
            self,
            "decided_at",
            _utc(
                self.decided_at
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
                if self.required_authority
                else None
            ),
            self.escalation_level.value,
            self.matched_rule_ids,
            self.reasons,
            self.decision_evidence,
            self.review_state.value,
            self.escalation_state.value,
            self.override_reference,
            self.override_authorization,
            self.appeal_review_reference,
            self.irreversible_action_protected,
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
                "other must GovernanceDecision."
            )

        if self.determinism_key != (
            other.determinism_key
        ):
            raise GovernanceDecisionConflictError(
                "Conflicting governance decisions."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": str(
                self.decision_id
            ),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "correlation_id": (
                self.correlation_id
            ),
            "policy_id": self.policy_id,
            "policy_version": (
                self.policy_version
            ),
            "policy_fingerprint": (
                self.policy_fingerprint
            ),
            "source_evaluation_fingerprint": (
                self.source_evaluation_fingerprint
            ),
            "decision_type": (
                self.decision_type.value
            ),
            "action_class": (
                self.action_class.value
            ),
            "approval_required": (
                self.approval_required
            ),
            "required_authority": (
                self.required_authority.value
                if self.required_authority
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
            "review_state": (
                self.review_state.value
            ),
            "escalation_state": (
                self.escalation_state.value
            ),
            "human_review_reference": (
                self.human_review_reference
            ),
            "decision_evidence": list(
                self.decision_evidence
            ),
            "override_reference": (
                self.override_reference
            ),
            "override_authorization": (
                self.override_authorization
            ),
            "appeal_review_reference": (
                self.appeal_review_reference
            ),
            "irreversible_action_protected": (
                self.irreversible_action_protected
            ),
            "decided_at": (
                self.decided_at.isoformat()
            ),
            "schema_version": (
                self.schema_version
            ),
            "fingerprint": self.fingerprint,
            "engine_version": (
                GOVERNANCE_DECISION_ENGINE_VERSION
            ),
        }


class GovernanceDecisionEngine:
    """Translate governance evaluation into decision state."""

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
                "evaluation must GovernanceEvaluation."
            )

        disposition = evaluation.disposition

        if disposition is (
            GovernanceDisposition.CONTINUE
        ):
            decision_type = (
                GovernanceDecisionType.CONTINUE
            )
            approval_required = False
            authority = None
            escalation = (
                GovernanceEscalationLevel.NONE
            )

        elif disposition is (
            GovernanceDisposition.REVIEW
        ):
            decision_type = (
                GovernanceDecisionType.REVIEW
            )
            approval_required = False
            authority = (
                GovernanceAuthorityClass
                .STANDARD_REVIEW
            )
            escalation = (
                GovernanceEscalationLevel.REVIEW
            )

        elif disposition is (
            GovernanceDisposition.APPROVAL_REQUIRED
        ):
            decision_type = (
                GovernanceDecisionType
                .APPROVAL_REQUIRED
            )
            approval_required = True
            authority = (
                GovernanceAuthorityClass
                .SENIOR_REVIEW
            )
            escalation = (
                GovernanceEscalationLevel.HIGH
            )

        elif disposition is (
            GovernanceDisposition.ESCALATE
        ):
            decision_type = (
                GovernanceDecisionType
                .ESCALATION_REQUIRED
            )
            approval_required = True
            authority = (
                GovernanceAuthorityClass
                .EXECUTIVE
            )
            escalation = (
                GovernanceEscalationLevel.CRITICAL
            )

        else:
            raise GovernanceDecisionError(
                "Unsupported governance disposition."
            )

        timestamp = _utc(
            decided_at
            or datetime.now(timezone.utc)
        )

        normalized_evidence = tuple(
            sorted(
                {
                    *evaluation.decision_evidence,
                    *evidence_references,
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
            "decision_type": (
                decision_type.value
            ),
            "action_class": (
                evaluation.action_class.value
            ),
            "approval_required": approval_required,
            "required_authority": (
                authority.value
                if authority
                else None
            ),
            "escalation_level": (
                escalation.value
            ),
            "matched_rule_ids": (
                evaluation.matched_rule_ids
            ),
            "reasons": evaluation.reasons,
            "decision_evidence": (
                normalized_evidence
            ),
            "review_state": (
                "NOT_REQUIRED"
                if decision_type
                is GovernanceDecisionType.CONTINUE
                else "PENDING"
            ),
            "escalation_state": (
                "NOT_REQUIRED"
                if escalation
                is GovernanceEscalationLevel.NONE
                else "OPEN"
            ),
            "irreversible_action_protected": True,
        }

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
            fingerprint=_fingerprint(
                material
            ),
            review_state=(
                GovernanceReviewState.NOT_REQUIRED
                if decision_type
                is GovernanceDecisionType.CONTINUE
                else GovernanceReviewState.PENDING
            ),
            escalation_state=(
                GovernanceEscalationState.NOT_REQUIRED
                if escalation
                is GovernanceEscalationLevel.NONE
                else GovernanceEscalationState.OPEN
            ),
            human_review_reference=(
                None
                if decision_type
                is GovernanceDecisionType.CONTINUE
                else (
                    f"human-review:"
                    f"{evaluation.correlation_id}"
                )
            ),
            decision_evidence=(
                normalized_evidence
            ),
            irreversible_action_protected=True,
        )


__all__ = [
    "GOVERNANCE_DECISION_SCHEMA_VERSION",
    "GOVERNANCE_DECISION_ENGINE_VERSION",
    "GovernanceDecisionError",
    "GovernanceDecisionValidationError",
    "GovernanceDecisionConflictError",
    "GovernanceDecisionType",
    "GovernanceAuthorityClass",
    "GovernanceEscalationLevel",
    "GovernanceReviewState",
    "GovernanceEscalationState",
    "GovernanceDecision",
    "GovernanceDecisionEngine",
]
