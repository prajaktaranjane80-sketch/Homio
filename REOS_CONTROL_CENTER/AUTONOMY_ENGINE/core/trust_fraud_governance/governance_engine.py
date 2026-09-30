"""CORE-007 T04 — governance policy evaluation authority.

Consumes the existing risk outputs and evaluates governance policy.

It does not:
- calculate trust,
- detect fraud,
- calculate risk,
- authorize actions,
- execute actions,
- persist Control Center state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID, uuid4

from .governance_policy import (
    GovernanceActionClass,
    GovernanceDisposition,
    GovernancePolicy,
    GovernancePolicyValidationError,
    GOVERNANCE_POLICY_ENGINE_VERSION,
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
    """Conflicting deterministic governance evaluation."""


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise GovernanceEvaluationError(
            "evaluated_at must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class GovernanceEvaluation:
    """Immutable governance interpretation of risk evidence."""

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
        )

    def assert_compatible(
        self,
        other: "GovernanceEvaluation",
    ) -> None:
        if self.determinism_key != other.determinism_key:
            raise GovernanceEvaluationConflictError(
                "Conflicting governance evaluations."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": str(self.evaluation_id),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "correlation_id": self.correlation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_fingerprint": self.policy_fingerprint,
            "action_class": self.action_class.value,
            "disposition": self.disposition.value,
            "matched_rule_ids": list(self.matched_rule_ids),
            "reasons": list(self.reasons),
            "risk_evaluation_fingerprint": (
                self.risk_evaluation_fingerprint
            ),
            "evaluated_at": self.evaluated_at.isoformat(),
            "fingerprint": self.fingerprint,
            "engine_version": GOVERNANCE_POLICY_ENGINE_VERSION,
        }


class GovernanceEngine:
    """Evaluates governance policy without becoming authorization."""

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
        if not isinstance(policy, GovernancePolicy):
            raise GovernancePolicyValidationError(
                "policy must be GovernancePolicy."
            )

        if not policy.is_active(evaluated_at):
            raise GovernanceEvaluationError(
                "Governance policy is inactive."
            )

        if not tenant_id or not subject_id:
            raise GovernanceScopeError(
                "tenant_id and subject_id are required."
            )

        if not correlation_id:
            raise GovernanceEvaluationError(
                "correlation_id is required."
            )

        action_class = (
            GovernanceActionClass.INFORMATIONAL
        )
        disposition = GovernanceDisposition.CONTINUE

        matched_rule_ids: list[str] = []
        reasons: list[str] = []

        risk_outcome = None
        risk_tenant = None
        risk_subject = None
        risk_fingerprint = None

        if risk_evaluation is not None:
            risk_tenant = getattr(
                risk_evaluation,
                "tenant_id",
                None,
            )
            risk_subject = getattr(
                risk_evaluation,
                "subject_id",
                None,
            )
            risk_outcome = getattr(
                risk_evaluation,
                "outcome",
                None,
            )
            risk_fingerprint = getattr(
                risk_evaluation,
                "fingerprint",
                None,
            )

            if risk_tenant != tenant_id:
                raise GovernanceScopeError(
                    "Risk evaluation belongs to another tenant."
                )

            if risk_subject != subject_id:
                raise GovernanceScopeError(
                    "Risk evaluation belongs to another subject."
                )

        for rule in policy.rules:
            if not rule.enabled:
                continue

            matches = self._matches(
                rule.action_class,
                risk_outcome,
                context or {},
            )

            if not matches:
                continue

            matched_rule_ids.append(rule.rule_id)
            reasons.append(rule.reason)

            if (
                self._rank(rule.action_class)
                > self._rank(action_class)
            ):
                action_class = rule.action_class

            if (
                self._disposition_rank(rule.disposition)
                > self._disposition_rank(disposition)
            ):
                disposition = rule.disposition

        timestamp = _utc(evaluated_at)

        fingerprint_payload = {
            "tenant_id": tenant_id,
            "subject_id": subject_id,
            "correlation_id": correlation_id,
            "policy_id": policy.policy_id,
            "policy_version": policy.version,
            "policy_fingerprint": policy.fingerprint,
            "action_class": action_class.value,
            "disposition": disposition.value,
            "matched_rule_ids": matched_rule_ids,
            "reasons": reasons,
            "risk_evaluation_fingerprint": risk_fingerprint,
            "evaluated_at": timestamp.isoformat(),
        }

        import hashlib
        import json

        raw = json.dumps(
            fingerprint_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        fingerprint = hashlib.sha256(raw).hexdigest()

        return GovernanceEvaluation(
            evaluation_id=evaluation_id or uuid4(),
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            policy_fingerprint=policy.fingerprint,
            action_class=action_class,
            disposition=disposition,
            matched_rule_ids=tuple(matched_rule_ids),
            reasons=tuple(reasons),
            risk_evaluation_fingerprint=risk_fingerprint,
            evaluated_at=timestamp,
            fingerprint=fingerprint,
        )

    @staticmethod
    def _rank(
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
        risk_outcome: Any,
        context: Mapping[str, Any],
    ) -> bool:
        if action_class is GovernanceActionClass.INFORMATIONAL:
            return True

        if risk_outcome is None:
            return False

        outcome_value = getattr(
            risk_outcome,
            "value",
            str(risk_outcome),
        )

        if action_class is GovernanceActionClass.REVIEW:
            return outcome_value in {
                "REVIEW",
                "HIGH",
                "CRITICAL",
            }

        if action_class is GovernanceActionClass.HIGH_RISK:
            return outcome_value in {
                "HIGH",
                "CRITICAL",
            }

        if action_class is GovernanceActionClass.CRITICAL:
            return outcome_value == "CRITICAL"

        return False
