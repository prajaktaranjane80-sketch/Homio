from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID, uuid4
import hashlib
import json

from .governance_policy import (
    GovernanceActionClass,
    GovernanceDisposition,
    GovernancePolicy,
    GovernancePolicyValidationError,
)
from .risk_rules import RiskRuleEvaluation


class GovernanceEvaluationError(ValueError):
    """Base governance evaluation error."""


class GovernanceScopeError(
    GovernanceEvaluationError
):
    """Tenant or subject mismatch."""


class GovernanceEvaluationConflictError(
    GovernanceEvaluationError
):
    """Conflicting governance evaluation."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceEvaluationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise GovernanceEvaluationError(
            "evaluated_at must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class GovernanceEvaluation:
    """Immutable governance interpretation.

    This remains descriptive governance output and is not
    an authorization verdict.
    """

    evaluation_id: UUID

    tenant_id: str
    subject_id: str
    correlation_id: str

    policy_id: str
    policy_version: str
    policy_fingerprint: str

    action_class: GovernanceActionClass
    disposition: GovernanceDisposition

    matched_rule_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    risk_evaluation_fingerprint: str | None

    evaluated_at: datetime
    fingerprint: str

    matched_rule_precedence: tuple[int, ...] = ()
    rule_provenance_references: tuple[
        str,
        ...
    ] = ()
    exception_references: tuple[str, ...] = ()

    decision_evidence: tuple[str, ...] = ()

    review_state: str = "PENDING"

    reproducibility: str = "DETERMINISTIC"

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "subject_id",
            "correlation_id",
            "policy_id",
            "policy_version",
            "policy_fingerprint",
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
            self.evaluation_id,
            UUID,
        ):
            raise GovernanceEvaluationError(
                "evaluation_id must UUID."
            )

        if not isinstance(
            self.action_class,
            GovernanceActionClass,
        ):
            raise GovernanceEvaluationError(
                "Invalid action_class."
            )

        if not isinstance(
            self.disposition,
            GovernanceDisposition,
        ):
            raise GovernanceEvaluationError(
                "Invalid disposition."
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
            "matched_rule_precedence",
            tuple(
                int(item)
                for item in self.matched_rule_precedence
            ),
        )

        object.__setattr__(
            self,
            "rule_provenance_references",
            tuple(
                _text(
                    item,
                    "rule_provenance_reference",
                )
                for item in (
                    self.rule_provenance_references
                )
            ),
        )

        object.__setattr__(
            self,
            "exception_references",
            tuple(
                _text(
                    item,
                    "exception_reference",
                )
                for item in self.exception_references
            ),
        )

        object.__setattr__(
            self,
            "decision_evidence",
            tuple(
                _text(
                    item,
                    "decision_evidence",
                )
                for item in self.decision_evidence
            ),
        )

        object.__setattr__(
            self,
            "evaluated_at",
            _utc(
                self.evaluated_at
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
            self.action_class.value,
            self.disposition.value,
            self.matched_rule_ids,
            self.reasons,
            self.risk_evaluation_fingerprint,
            self.matched_rule_precedence,
            self.rule_provenance_references,
            self.exception_references,
            self.decision_evidence,
        )

    def assert_compatible(
        self,
        other: "GovernanceEvaluation",
    ) -> None:
        if not isinstance(
            other,
            GovernanceEvaluation,
        ):
            raise GovernanceEvaluationError(
                "other must GovernanceEvaluation."
            )

        if self.determinism_key != (
            other.determinism_key
        ):
            raise GovernanceEvaluationConflictError(
                "Conflicting governance evaluations."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": str(
                self.evaluation_id
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
            "action_class": (
                self.action_class.value
            ),
            "disposition": (
                self.disposition.value
            ),
            "matched_rule_ids": list(
                self.matched_rule_ids
            ),
            "matched_rule_precedence": list(
                self.matched_rule_precedence
            ),
            "reasons": list(self.reasons),
            "risk_evaluation_fingerprint": (
                self.risk_evaluation_fingerprint
            ),
            "evaluated_at": (
                self.evaluated_at.isoformat()
            ),
            "rule_provenance_references": list(
                self.rule_provenance_references
            ),
            "exception_references": list(
                self.exception_references
            ),
            "decision_evidence": list(
                self.decision_evidence
            ),
            "review_state": self.review_state,
            "reproducibility": (
                self.reproducibility
            ),
            "fingerprint": self.fingerprint,
        }


class GovernanceEngine:
    """
    Governance policy evaluation authority.

    It interprets rules.

    It does not:
    - authorize actors,
    - approve transactions,
    - execute business actions,
    - own Control Center state,
    - own event transport,
    - own ACRL.
    """

    def evaluate(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        correlation_id: str,
        policy: GovernancePolicy,
        risk_evaluation: RiskRuleEvaluation | None = None,
        context: Mapping[str, Any] | None = None,
        evaluated_at: datetime,
        evaluation_id: UUID | None = None,
    ) -> GovernanceEvaluation:
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )

        subject_id = _text(
            subject_id,
            "subject_id",
        )

        correlation_id = _text(
            correlation_id,
            "correlation_id",
        )

        if not isinstance(
            policy,
            GovernancePolicy,
        ):
            raise GovernancePolicyValidationError(
                "policy must be GovernancePolicy."
            )

        timestamp = _utc(
            evaluated_at
        )

        if not policy.is_active(timestamp):
            raise GovernanceEvaluationError(
                "Governance policy is inactive."
            )

        context = dict(context or {})

        if not policy.applies_to(
            tenant_id=tenant_id,
            subject_id=subject_id,
            context=context,
        ):
            raise GovernanceScopeError(
                "Governance policy does not apply."
            )

        risk_outcome: str | None = None
        risk_fingerprint: str | None = None

        if risk_evaluation is not None:
            if (
                risk_evaluation.tenant_id
                != tenant_id
                or risk_evaluation.subject_id
                != subject_id
            ):
                raise GovernanceScopeError(
                    "Risk evaluation crosses governance scope."
                )

            risk_outcome = (
                risk_evaluation.outcome.value
            )
            risk_fingerprint = (
                risk_evaluation.fingerprint
            )

        matches = []

        for rule in policy.rules:
            if not rule.enabled:
                continue

            if not rule.applies_to(
                tenant_id=tenant_id,
                subject_id=subject_id,
                risk_outcome=risk_outcome,
                context=context,
            ):
                continue

            if not self._matches(
                rule.action_class,
                risk_outcome,
                context,
            ):
                continue

            matches.append(rule)

        matches.sort(
            key=lambda rule: (
                -self._action_rank(
                    rule.action_class
                ),
                -self._disposition_rank(
                    rule.disposition
                ),
                -rule.effective_precedence,
                rule.rule_id,
                rule.version,
            )
        )

        action_class = (
            matches[0].action_class
            if matches
            else GovernanceActionClass.INFORMATIONAL
        )

        disposition = (
            matches[0].disposition
            if matches
            else GovernanceDisposition.CONTINUE
        )

        matched_ids = tuple(
            rule.rule_id
            for rule in matches
        )

        reasons = tuple(
            rule.reason
            for rule in matches
        )

        precedences = tuple(
            rule.effective_precedence
            for rule in matches
        )

        provenance = tuple(
            sorted(
                {
                    rule.provenance_reference
                    for rule in matches
                }
            )
        )

        exceptions = tuple(
            sorted(
                {
                    rule.exception_reference
                    for rule in matches
                    if rule.exception_reference
                }
            )
        )

        decision_evidence = tuple(
            sorted(
                {
                    *(
                        str(item)
                        for item in context.get(
                            "evidence_references",
                            (),
                        )
                    ),
                    *(
                        risk_evaluation.evidence_references
                        if risk_evaluation is not None
                        else ()
                    ),
                }
            )
        )

        material = {
            "tenant_id": tenant_id,
            "subject_id": subject_id,
            "correlation_id": correlation_id,
            "policy_id": policy.policy_id,
            "policy_version": policy.version,
            "policy_fingerprint": (
                policy.fingerprint
            ),
            "action_class": action_class.value,
            "disposition": disposition.value,
            "matched_rule_ids": matched_ids,
            "reasons": reasons,
            "risk_evaluation_fingerprint": (
                risk_fingerprint
            ),
            "matched_rule_precedence": (
                precedences
            ),
            "rule_provenance_references": (
                provenance
            ),
            "exception_references": exceptions,
            "decision_evidence": (
                decision_evidence
            ),
        }

        return GovernanceEvaluation(
            evaluation_id=(
                evaluation_id
                or uuid4()
            ),
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            policy_fingerprint=(
                policy.fingerprint
            ),
            action_class=action_class,
            disposition=disposition,
            matched_rule_ids=matched_ids,
            reasons=reasons,
            risk_evaluation_fingerprint=(
                risk_fingerprint
            ),
            evaluated_at=timestamp,
            fingerprint=_fingerprint(
                material
            ),
            matched_rule_precedence=(
                precedences
            ),
            rule_provenance_references=(
                provenance
            ),
            exception_references=exceptions,
            decision_evidence=(
                decision_evidence
            ),
            review_state=(
                "PENDING"
                if disposition
                is not GovernanceDisposition.CONTINUE
                else "NOT_REQUIRED"
            ),
        )

    @staticmethod
    def _action_rank(
        action_class: GovernanceActionClass,
    ) -> int:
        return {
            GovernanceActionClass.INFORMATIONAL: 0,
            GovernanceActionClass.REVIEW: 1,
            GovernanceActionClass.HIGH_RISK: 2,
            GovernanceActionClass.CRITICAL: 3,
        }[action_class]

    @staticmethod
    def _disposition_rank(
        disposition: GovernanceDisposition,
    ) -> int:
        return {
            GovernanceDisposition.CONTINUE: 0,
            GovernanceDisposition.REVIEW: 1,
            GovernanceDisposition.APPROVAL_REQUIRED: 2,
            GovernanceDisposition.ESCALATE: 3,
        }[disposition]

    @staticmethod
    def _matches(
        action_class: GovernanceActionClass,
        risk_outcome: str | None,
        context: Mapping[str, Any],
    ) -> bool:
        if action_class is (
            GovernanceActionClass.INFORMATIONAL
        ):
            return True

        if risk_outcome is None:
            return False

        if action_class is (
            GovernanceActionClass.REVIEW
        ):
            return risk_outcome in {
                "REVIEW",
                "HIGH",
                "CRITICAL",
            }

        if action_class is (
            GovernanceActionClass.HIGH_RISK
        ):
            return risk_outcome in {
                "HIGH",
                "CRITICAL",
            }

        if action_class is (
            GovernanceActionClass.CRITICAL
        ):
            return risk_outcome == "CRITICAL"

        return False


__all__ = [
    "GovernanceEvaluationError",
    "GovernanceScopeError",
    "GovernanceEvaluationConflictError",
    "GovernanceEvaluation",
    "GovernanceEngine",
]
