"""CORE-007 T03 — deterministic risk rule evaluation.

ARCH-017 bounded risk-rule evaluation authority.

This module:
- consumes the existing TrustScore authority,
- consumes the existing FraudAssessment authority,
- evaluates versioned, immutable rules,
- produces reproducible, evidence-linked risk classifications.

This module does NOT:
- calculate trust scores,
- detect fraud,
- own governance approval,
- authorize or deny actions,
- execute irreversible actions,
- publish events,
- own Control Center state,
- own ACRL state,
- create a parallel evidence/checkpoint system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping
from uuid import UUID, uuid4

from .fraud_detection import (
    FraudAssessment,
    FraudSeverity,
)
from .trust_score import TrustScore


RISK_RULE_SCHEMA_VERSION = 1
RISK_RULE_ENGINE_VERSION = "1.0"


class RiskRuleError(ValueError):
    """Base risk-rule error."""


class RiskRuleValidationError(RiskRuleError):
    """Invalid risk-rule contract data."""


class RiskRuleScopeError(RiskRuleError):
    """Cross-tenant or subject-scope violation."""


class RiskRuleConflictError(RiskRuleError):
    """Conflicting rule, policy or evaluation identity."""


class RiskRuleOutcome(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskRuleCondition(str, Enum):
    FRAUD_SEVERITY = "FRAUD_SEVERITY"
    FRAUD_TRIPWIRE = "FRAUD_TRIPWIRE"
    TRUST_SCORE_RANGE = "TRUST_SCORE_RANGE"


_OUTCOME_RANK: dict[RiskRuleOutcome, int] = {
    RiskRuleOutcome.INFORMATIONAL: 0,
    RiskRuleOutcome.REVIEW: 1,
    RiskRuleOutcome.HIGH: 2,
    RiskRuleOutcome.CRITICAL: 3,
}


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RiskRuleValidationError(
            f"{field_name} must be non-empty text."
        )

    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise RiskRuleValidationError(
            f"{field_name} must be an integer >= 1."
        )

    return value


def _score(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 100
    ):
        raise RiskRuleValidationError(
            f"{field_name} must be an integer between 0 and 100."
        )

    return value


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise RiskRuleValidationError(
            f"{field_name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise RiskRuleValidationError(
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

    if isinstance(value, Mapping):
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
        isinstance(value, (str, int, float, bool))
        or value is None
    ):
        return value

    raise RiskRuleValidationError(
        "Unsupported value type: "
        f"{type(value).__name__}"
    )


def _fingerprint(value: Any) -> str:
    payload = json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class RiskRule:
    """Immutable versioned declarative risk rule."""

    rule_id: str
    version: str
    priority: int
    condition: RiskRuleCondition
    outcome: RiskRuleOutcome
    description: str

    fraud_severity: FraudSeverity | None = None

    min_trust_score: int | None = None
    max_trust_score: int | None = None

    enabled: bool = True

    effective_at: datetime | None = None
    expires_at: datetime | None = None

    source_reference: str = "CORE-007-T03"

    schema_version: int = RISK_RULE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rule_id",
            _text(self.rule_id, "rule_id"),
        )

        object.__setattr__(
            self,
            "version",
            _text(self.version, "version"),
        )

        object.__setattr__(
            self,
            "priority",
            _positive_int(self.priority, "priority"),
        )

        object.__setattr__(
            self,
            "description",
            _text(
                self.description,
                "description",
            ),
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

        if not isinstance(
            self.condition,
            RiskRuleCondition,
        ):
            raise RiskRuleValidationError(
                "condition must be RiskRuleCondition."
            )

        if not isinstance(
            self.outcome,
            RiskRuleOutcome,
        ):
            raise RiskRuleValidationError(
                "outcome must be RiskRuleOutcome."
            )

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise RiskRuleValidationError(
                "enabled must be boolean."
            )

        if (
            self.schema_version
            != RISK_RULE_SCHEMA_VERSION
        ):
            raise RiskRuleValidationError(
                "Unsupported Risk Rule schema version."
            )

        effective_at = (
            _utc(
                self.effective_at,
                "effective_at",
            )
            if self.effective_at is not None
            else None
        )

        expires_at = (
            _utc(
                self.expires_at,
                "expires_at",
            )
            if self.expires_at is not None
            else None
        )

        if (
            effective_at is not None
            and expires_at is not None
            and expires_at <= effective_at
        ):
            raise RiskRuleValidationError(
                "expires_at must be after effective_at."
            )

        object.__setattr__(
            self,
            "effective_at",
            effective_at,
        )

        object.__setattr__(
            self,
            "expires_at",
            expires_at,
        )

        if self.min_trust_score is not None:
            _score(
                self.min_trust_score,
                "min_trust_score",
            )

        if self.max_trust_score is not None:
            _score(
                self.max_trust_score,
                "max_trust_score",
            )

        if (
            self.min_trust_score is not None
            and self.max_trust_score is not None
            and self.max_trust_score
            < self.min_trust_score
        ):
            raise RiskRuleValidationError(
                "max_trust_score must be >= min_trust_score."
            )

        if (
            self.condition
            is RiskRuleCondition.FRAUD_SEVERITY
        ):
            if not isinstance(
                self.fraud_severity,
                FraudSeverity,
            ):
                raise RiskRuleValidationError(
                    "fraud_severity is required for FRAUD_SEVERITY."
                )

            if (
                self.min_trust_score is not None
                or self.max_trust_score is not None
            ):
                raise RiskRuleValidationError(
                    "Trust-score bounds are invalid "
                    "for FRAUD_SEVERITY."
                )

        elif (
            self.condition
            is RiskRuleCondition.FRAUD_TRIPWIRE
        ):
            if self.fraud_severity is not None:
                raise RiskRuleValidationError(
                    "fraud_severity is invalid "
                    "for FRAUD_TRIPWIRE."
                )

            if (
                self.min_trust_score is not None
                or self.max_trust_score is not None
            ):
                raise RiskRuleValidationError(
                    "Trust-score bounds are invalid "
                    "for FRAUD_TRIPWIRE."
                )

        elif (
            self.condition
            is RiskRuleCondition.TRUST_SCORE_RANGE
        ):
            if (
                self.min_trust_score is None
                and self.max_trust_score is None
            ):
                raise RiskRuleValidationError(
                    "At least one trust-score bound "
                    "is required."
                )

            if self.fraud_severity is not None:
                raise RiskRuleValidationError(
                    "fraud_severity is invalid "
                    "for TRUST_SCORE_RANGE."
                )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.rule_id,
            self.version,
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "rule_id": self.rule_id,
                "version": self.version,
                "priority": self.priority,
                "condition": self.condition,
                "outcome": self.outcome,
                "description": self.description,
                "fraud_severity": self.fraud_severity,
                "min_trust_score": self.min_trust_score,
                "max_trust_score": self.max_trust_score,
                "enabled": self.enabled,
                "effective_at": self.effective_at,
                "expires_at": self.expires_at,
                "source_reference": self.source_reference,
                "schema_version": self.schema_version,
            }
        )

    def is_active(
        self,
        evaluated_at: datetime,
    ) -> bool:
        when = _utc(
            evaluated_at,
            "evaluated_at",
        )

        return (
            self.enabled
            and (
                self.effective_at is None
                or when >= self.effective_at
            )
            and (
                self.expires_at is None
                or when < self.expires_at
            )
        )

    def matches(
        self,
        *,
        trust_score: TrustScore | None,
        fraud_assessment: FraudAssessment | None,
    ) -> bool:
        if (
            self.condition
            is RiskRuleCondition.FRAUD_SEVERITY
        ):
            return bool(
                fraud_assessment is not None
                and any(
                    finding.severity
                    is self.fraud_severity
                    for finding
                    in fraud_assessment.findings
                )
            )

        if (
            self.condition
            is RiskRuleCondition.FRAUD_TRIPWIRE
        ):
            return bool(
                fraud_assessment is not None
                and fraud_assessment.tripwire_raised
            )

        if (
            self.condition
            is RiskRuleCondition.TRUST_SCORE_RANGE
        ):
            if trust_score is None:
                return False

            if (
                self.min_trust_score is not None
                and trust_score.score
                < self.min_trust_score
            ):
                return False

            if (
                self.max_trust_score is not None
                and trust_score.score
                > self.max_trust_score
            ):
                return False

            return True

        raise RiskRuleValidationError(
            "Unsupported risk rule condition."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "version": self.version,
            "priority": self.priority,
            "condition": self.condition.value,
            "outcome": self.outcome.value,
            "description": self.description,
            "fraud_severity": (
                self.fraud_severity.value
                if self.fraud_severity is not None
                else None
            ),
            "min_trust_score": (
                self.min_trust_score
            ),
            "max_trust_score": (
                self.max_trust_score
            ),
            "enabled": self.enabled,
            "effective_at": (
                self.effective_at.isoformat()
                if self.effective_at is not None
                else None
            ),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at is not None
                else None
            ),
            "source_reference": (
                self.source_reference
            ),
            "schema_version": (
                self.schema_version
            ),
            "fingerprint": (
                self.fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class RiskRulePolicy:
    """Immutable, versioned and fingerprinted risk policy."""

    policy_id: str
    version: str
    rules: tuple[RiskRule, ...]

    default_outcome: RiskRuleOutcome = (
        RiskRuleOutcome.INFORMATIONAL
    )

    effective_at: datetime | None = None
    expires_at: datetime | None = None

    schema_version: int = (
        RISK_RULE_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
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
            "version",
            _text(
                self.version,
                "version",
            ),
        )

        if not isinstance(
            self.rules,
            tuple,
        ):
            raise RiskRuleValidationError(
                "rules must be tuple."
            )

        if not isinstance(
            self.default_outcome,
            RiskRuleOutcome,
        ):
            raise RiskRuleValidationError(
                "default_outcome must be RiskRuleOutcome."
            )

        if (
            self.schema_version
            != RISK_RULE_SCHEMA_VERSION
        ):
            raise RiskRuleValidationError(
                "Unsupported Risk Rule policy schema version."
            )

        seen: set[tuple[str, str]] = set()

        for rule in self.rules:
            if not isinstance(
                rule,
                RiskRule,
            ):
                raise RiskRuleValidationError(
                    "rules must contain RiskRule."
                )

            if rule.identity_key in seen:
                raise RiskRuleConflictError(
                    "Duplicate RiskRule identity in policy."
                )

            seen.add(rule.identity_key)

        effective_at = (
            _utc(
                self.effective_at,
                "effective_at",
            )
            if self.effective_at is not None
            else None
        )

        expires_at = (
            _utc(
                self.expires_at,
                "expires_at",
            )
            if self.expires_at is not None
            else None
        )

        if (
            effective_at is not None
            and expires_at is not None
            and expires_at <= effective_at
        ):
            raise RiskRuleValidationError(
                "expires_at must be after effective_at."
            )

        object.__setattr__(
            self,
            "effective_at",
            effective_at,
        )

        object.__setattr__(
            self,
            "expires_at",
            expires_at,
        )

        object.__setattr__(
            self,
            "rules",
            tuple(
                sorted(
                    self.rules,
                    key=lambda item: (
                        -item.priority,
                        item.rule_id,
                        item.version,
                    ),
                )
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.policy_id,
            self.version,
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "policy_id": self.policy_id,
                "version": self.version,
                "rules": tuple(
                    item.fingerprint
                    for item in self.rules
                ),
                "default_outcome": (
                    self.default_outcome
                ),
                "effective_at": (
                    self.effective_at
                ),
                "expires_at": (
                    self.expires_at
                ),
                "schema_version": (
                    self.schema_version
                ),
            }
        )

    def assert_compatible(
        self,
        other: "RiskRulePolicy",
    ) -> None:
        if not isinstance(
            other,
            RiskRulePolicy,
        ):
            raise RiskRuleValidationError(
                "other must be RiskRulePolicy."
            )

        if (
            self.identity_key
            != other.identity_key
        ):
            raise RiskRuleConflictError(
                "Risk-rule policy identities differ."
            )

        if (
            self.fingerprint
            != other.fingerprint
        ):
            raise RiskRuleConflictError(
                "Same Risk-rule policy identity "
                "has conflicting data."
            )

    def is_active(
        self,
        evaluated_at: datetime,
    ) -> bool:
        when = _utc(
            evaluated_at,
            "evaluated_at",
        )

        return (
            (
                self.effective_at is None
                or when >= self.effective_at
            )
            and (
                self.expires_at is None
                or when < self.expires_at
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "rules": [
                item.to_dict()
                for item in self.rules
            ],
            "default_outcome": (
                self.default_outcome.value
            ),
            "effective_at": (
                self.effective_at.isoformat()
                if self.effective_at is not None
                else None
            ),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at is not None
                else None
            ),
            "schema_version": (
                self.schema_version
            ),
            "fingerprint": (
                self.fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class RiskRuleEvaluation:
    """Immutable evidence-linked risk classification."""

    evaluation_id: UUID

    tenant_id: str
    subject_id: str
    correlation_id: str

    engine_version: str

    policy_id: str
    policy_version: str
    policy_fingerprint: str

    outcome: RiskRuleOutcome

    matched_rule_ids: tuple[str, ...]
    matched_rule_fingerprints: tuple[str, ...]

    trust_score: int | None

    fraud_assessment_fingerprint: str | None

    evidence_references: tuple[str, ...]

    evaluated_at: datetime

    source_of_truth: str = "risk_rules"

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation_id,
            UUID,
        ):
            raise RiskRuleValidationError(
                "evaluation_id must be UUID."
            )

        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "subject_id",
            _text(
                self.subject_id,
                "subject_id",
            ),
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
            "engine_version",
            _text(
                self.engine_version,
                "engine_version",
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

        if not isinstance(
            self.outcome,
            RiskRuleOutcome,
        ):
            raise RiskRuleValidationError(
                "outcome must be RiskRuleOutcome."
            )

        if not isinstance(
            self.matched_rule_ids,
            tuple,
        ):
            raise RiskRuleValidationError(
                "matched_rule_ids must be tuple."
            )

        if not isinstance(
            self.matched_rule_fingerprints,
            tuple,
        ):
            raise RiskRuleValidationError(
                "matched_rule_fingerprints "
                "must be tuple."
            )

        if (
            len(self.matched_rule_ids)
            != len(
                self.matched_rule_fingerprints
            )
        ):
            raise RiskRuleValidationError(
                "Matched rule identities and "
                "fingerprints differ."
            )

        object.__setattr__(
            self,
            "matched_rule_ids",
            tuple(
                _text(
                    item,
                    "matched_rule_id",
                )
                for item
                in self.matched_rule_ids
            ),
        )

        object.__setattr__(
            self,
            "matched_rule_fingerprints",
            tuple(
                _text(
                    item,
                    "matched_rule_fingerprint",
                )
                for item
                in self.matched_rule_fingerprints
            ),
        )

        if self.trust_score is not None:
            _score(
                self.trust_score,
                "trust_score",
            )

        if (
            self.fraud_assessment_fingerprint
            is not None
        ):
            _text(
                self.fraud_assessment_fingerprint,
                "fraud_assessment_fingerprint",
            )

        object.__setattr__(
            self,
            "evidence_references",
            tuple(
                _text(
                    item,
                    "evidence_reference",
                )
                for item
                in self.evidence_references
            ),
        )

        object.__setattr__(
            self,
            "evaluated_at",
            _utc(
                self.evaluated_at,
                "evaluated_at",
            ),
        )

        if (
            self.source_of_truth
            != "risk_rules"
        ):
            raise RiskRuleValidationError(
                "source_of_truth must be risk_rules."
            )

    @property
    def identity_key(self) -> tuple[
        str,
        str,
        str,
        str,
        UUID,
    ]:
        return (
            self.tenant_id,
            self.subject_id,
            self.correlation_id,
            self.policy_version,
            self.evaluation_id,
        )

    @property
    def requires_review(self) -> bool:
        return (
            self.outcome
            is not RiskRuleOutcome.INFORMATIONAL
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            self._fingerprint_payload()
        )

    def _fingerprint_payload(
        self,
    ) -> dict[str, Any]:
        return {
            "evaluation_id": str(
                self.evaluation_id
            ),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "correlation_id": self.correlation_id,
            "engine_version": self.engine_version,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_fingerprint": (
                self.policy_fingerprint
            ),
            "outcome": self.outcome,
            "matched_rule_ids": (
                self.matched_rule_ids
            ),
            "matched_rule_fingerprints": (
                self.matched_rule_fingerprints
            ),
            "trust_score": self.trust_score,
            "fraud_assessment_fingerprint": (
                self.fraud_assessment_fingerprint
            ),
            "evidence_references": (
                self.evidence_references
            ),
            "evaluated_at": self.evaluated_at,
            "source_of_truth": (
                self.source_of_truth
            ),
        }

    def assert_compatible(
        self,
        other: "RiskRuleEvaluation",
    ) -> None:
        if not isinstance(
            other,
            RiskRuleEvaluation,
        ):
            raise RiskRuleValidationError(
                "other must be RiskRuleEvaluation."
            )

        if (
            self.identity_key
            != other.identity_key
        ):
            raise RiskRuleConflictError(
                "Risk evaluation identities differ."
            )

        if (
            self.fingerprint
            != other.fingerprint
        ):
            raise RiskRuleConflictError(
                "Same risk evaluation identity "
                "has conflicting data."
            )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "evaluation_id": str(
                self.evaluation_id
            ),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "correlation_id": self.correlation_id,
            "engine_version": self.engine_version,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_fingerprint": (
                self.policy_fingerprint
            ),
            "outcome": self.outcome.value,
            "matched_rule_ids": list(
                self.matched_rule_ids
            ),
            "matched_rule_fingerprints": list(
                self.matched_rule_fingerprints
            ),
            "trust_score": self.trust_score,
            "fraud_assessment_fingerprint": (
                self.fraud_assessment_fingerprint
            ),
            "evidence_references": list(
                self.evidence_references
            ),
            "evaluated_at": (
                self.evaluated_at.isoformat()
            ),
            "source_of_truth": (
                self.source_of_truth
            ),
        }

        if include_fingerprint:
            payload["fingerprint"] = (
                self.fingerprint
            )

        return payload


class RiskRuleEngine:
    """ARCH-017 bounded deterministic risk evaluator."""

    @staticmethod
    def _validate_scope(
        *,
        tenant_id: str,
        subject_id: str,
        trust_score: TrustScore | None,
        fraud_assessment: FraudAssessment | None,
    ) -> None:
        if trust_score is not None:
            if not isinstance(
                trust_score,
                TrustScore,
            ):
                raise RiskRuleValidationError(
                    "trust_score must be TrustScore or None."
                )

            if (
                trust_score.tenant_id
                != tenant_id
                or trust_score.subject_id
                != subject_id
            ):
                raise RiskRuleScopeError(
                    "Trust score crosses tenant "
                    "or subject scope."
                )

        if fraud_assessment is not None:
            if not isinstance(
                fraud_assessment,
                FraudAssessment,
            ):
                raise RiskRuleValidationError(
                    "fraud_assessment must be "
                    "FraudAssessment or None."
                )

            if (
                str(fraud_assessment.tenant_id)
                != tenant_id
                or str(fraud_assessment.subject_id)
                != subject_id
            ):
                raise RiskRuleScopeError(
                    "Fraud assessment crosses tenant "
                    "or subject scope."
                )

    @staticmethod
    def _evidence(
        *,
        trust_score: TrustScore | None,
        fraud_assessment: FraudAssessment | None,
    ) -> tuple[str, ...]:
        references: list[str] = []

        if fraud_assessment is not None:
            for finding in (
                fraud_assessment.findings
            ):
                references.extend(
                    finding.evidence_references
                )
                references.extend(
                    finding.source_references
                )

        if trust_score is not None:
            references.extend(
                trust_score.signal_fingerprints
            )
            references.append(
                trust_score.model_fingerprint
            )

        return tuple(
            dict.fromkeys(
                references
            )
        )

    def evaluate(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        correlation_id: str,
        policy: RiskRulePolicy,
        trust_score: TrustScore | None = None,
        fraud_assessment: FraudAssessment | None = None,
        evaluated_at: datetime | None = None,
        evaluation_id: UUID | None = None,
    ) -> RiskRuleEvaluation:
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
            RiskRulePolicy,
        ):
            raise RiskRuleValidationError(
                "policy must be RiskRulePolicy."
            )

        when = _utc(
            evaluated_at
            or datetime.now(timezone.utc),
            "evaluated_at",
        )

        if not policy.is_active(
            when
        ):
            raise RiskRuleValidationError(
                "Risk-rule policy is not active "
                "at evaluation time."
            )

        self._validate_scope(
            tenant_id=tenant_id,
            subject_id=subject_id,
            trust_score=trust_score,
            fraud_assessment=fraud_assessment,
        )

        matches = [
            rule
            for rule
            in policy.rules
            if rule.is_active(when)
            and rule.matches(
                trust_score=trust_score,
                fraud_assessment=fraud_assessment,
            )
        ]

        matches.sort(
            key=lambda rule: (
                -_OUTCOME_RANK[
                    rule.outcome
                ],
                -rule.priority,
                rule.rule_id,
                rule.version,
            )
        )

        outcome = (
            matches[0].outcome
            if matches
            else policy.default_outcome
        )

        return RiskRuleEvaluation(
            evaluation_id=(
                evaluation_id
                or uuid4()
            ),
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            engine_version=(
                RISK_RULE_ENGINE_VERSION
            ),
            policy_id=policy.policy_id,
            policy_version=policy.version,
            policy_fingerprint=(
                policy.fingerprint
            ),
            outcome=outcome,
            matched_rule_ids=tuple(
                item.rule_id
                for item in matches
            ),
            matched_rule_fingerprints=tuple(
                item.fingerprint
                for item in matches
            ),
            trust_score=(
                trust_score.score
                if trust_score is not None
                else None
            ),
            fraud_assessment_fingerprint=(
                fraud_assessment.fingerprint
                if fraud_assessment is not None
                else None
            ),
            evidence_references=self._evidence(
                trust_score=trust_score,
                fraud_assessment=fraud_assessment,
            ),
            evaluated_at=when,
        )


def default_fraud_risk_policy() -> RiskRulePolicy:
    """Baseline policy derived from existing FraudSeverity semantics."""

    return RiskRulePolicy(
        policy_id="CORE-007-FRAUD-BASELINE",
        version="1.0",
        rules=(
            RiskRule(
                rule_id=(
                    "FRAUD-SEVERITY-CRITICAL"
                ),
                version="1.0",
                priority=100,
                condition=(
                    RiskRuleCondition.FRAUD_SEVERITY
                ),
                outcome=(
                    RiskRuleOutcome.CRITICAL
                ),
                description=(
                    "Existing CRITICAL fraud finding "
                    "maps to CRITICAL risk."
                ),
                fraud_severity=(
                    FraudSeverity.CRITICAL
                ),
            ),
            RiskRule(
                rule_id=(
                    "FRAUD-SEVERITY-HIGH"
                ),
                version="1.0",
                priority=90,
                condition=(
                    RiskRuleCondition.FRAUD_SEVERITY
                ),
                outcome=(
                    RiskRuleOutcome.HIGH
                ),
                description=(
                    "Existing HIGH fraud finding "
                    "maps to HIGH risk."
                ),
                fraud_severity=(
                    FraudSeverity.HIGH
                ),
            ),
            RiskRule(
                rule_id=(
                    "FRAUD-SEVERITY-REVIEW"
                ),
                version="1.0",
                priority=80,
                condition=(
                    RiskRuleCondition.FRAUD_SEVERITY
                ),
                outcome=(
                    RiskRuleOutcome.REVIEW
                ),
                description=(
                    "Existing REVIEW fraud finding "
                    "maps to REVIEW risk."
                ),
                fraud_severity=(
                    FraudSeverity.REVIEW
                ),
            ),
            RiskRule(
                rule_id=(
                    "FRAUD-TRIPWIRE"
                ),
                version="1.0",
                priority=70,
                condition=(
                    RiskRuleCondition.FRAUD_TRIPWIRE
                ),
                outcome=(
                    RiskRuleOutcome.HIGH
                ),
                description=(
                    "Existing fraud tripwire "
                    "maps to HIGH risk."
                ),
            ),
        ),
    )


__all__ = [
    "RISK_RULE_ENGINE_VERSION",
    "RISK_RULE_SCHEMA_VERSION",
    "RiskRule",
    "RiskRuleCondition",
    "RiskRuleConflictError",
    "RiskRuleError",
    "RiskRuleEvaluation",
    "RiskRuleOutcome",
    "RiskRulePolicy",
    "RiskRuleScopeError",
    "RiskRuleValidationError",
    "RiskRuleEngine",
    "default_fraud_risk_policy",
]
