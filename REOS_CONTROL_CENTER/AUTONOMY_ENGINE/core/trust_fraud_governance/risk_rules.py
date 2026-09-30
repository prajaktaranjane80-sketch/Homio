from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4
import hashlib
import json

from .trust_score import TrustScore
from .fraud_detection import (
    FraudAssessment,
    FraudSeverity,
)


RISK_RULE_SCHEMA_VERSION = 1
RISK_RULE_ENGINE_VERSION = "1.0"


class RiskRuleError(ValueError):
    """Base deterministic risk-rule error."""


class RiskRuleValidationError(RiskRuleError):
    """Invalid risk-rule contract."""


class RiskRuleScopeError(RiskRuleError):
    """Tenant or subject mismatch."""


class RiskRuleConflictError(RiskRuleError):
    """Conflicting rule identity."""


class RiskRuleOutcome(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskRuleCondition(str, Enum):
    FRAUD_SEVERITY = "FRAUD_SEVERITY"
    FRAUD_TRIPWIRE = "FRAUD_TRIPWIRE"
    TRUST_SCORE_RANGE = "TRUST_SCORE_RANGE"


_OUTCOME_RANK = {
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
            f"{field_name} must be integer >= 1."
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
            f"{field_name} must be between 0 and 100."
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
        return _utc(
            value,
            "datetime",
        ).isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda item: str(item[0]),
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

    raise RiskRuleValidationError(
        "Unsupported canonical type."
    )


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class RiskRule:
    """Immutable deterministic versioned risk rule."""

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
    schema_version: int = (
        RISK_RULE_SCHEMA_VERSION
    )

    scope: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    applicability: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    precedence: int | None = None

    exception_reference: str | None = None

    provenance_reference: str = (
        "CORE-007.RISK_RULE"
    )

    def __post_init__(self) -> None:
        for name in (
            "rule_id",
            "version",
            "description",
            "source_reference",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                name,
                _text(
                    getattr(self, name),
                    name,
                ),
            )

        object.__setattr__(
            self,
            "priority",
            _positive_int(
                self.priority,
                "priority",
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

        if self.min_trust_score is not None:
            object.__setattr__(
                self,
                "min_trust_score",
                _score(
                    self.min_trust_score,
                    "min_trust_score",
                ),
            )

        if self.max_trust_score is not None:
            object.__setattr__(
                self,
                "max_trust_score",
                _score(
                    self.max_trust_score,
                    "max_trust_score",
                ),
            )

        if (
            self.min_trust_score is not None
            and self.max_trust_score is not None
            and self.min_trust_score
            > self.max_trust_score
        ):
            raise RiskRuleValidationError(
                "min_trust_score cannot exceed max."
            )

        if (
            self.effective_at is not None
        ):
            object.__setattr__(
                self,
                "effective_at",
                _utc(
                    self.effective_at,
                    "effective_at",
                ),
            )

        if self.expires_at is not None:
            object.__setattr__(
                self,
                "expires_at",
                _utc(
                    self.expires_at,
                    "expires_at",
                ),
            )

        if (
            self.effective_at is not None
            and self.expires_at is not None
            and self.expires_at
            <= self.effective_at
        ):
            raise RiskRuleValidationError(
                "expires_at must be after effective_at."
            )

        if self.schema_version != (
            RISK_RULE_SCHEMA_VERSION
        ):
            raise RiskRuleValidationError(
                "Unsupported risk rule schema."
            )

        if self.precedence is not None:
            object.__setattr__(
                self,
                "precedence",
                _positive_int(
                    self.precedence,
                    "precedence",
                ),
            )

        if not isinstance(
            self.scope,
            Mapping,
        ):
            raise RiskRuleValidationError(
                "scope must be mapping."
            )

        if not isinstance(
            self.applicability,
            Mapping,
        ):
            raise RiskRuleValidationError(
                "applicability must be mapping."
            )

        object.__setattr__(
            self,
            "scope",
            dict(
                _canonicalize(
                    self.scope
                )
            ),
        )

        object.__setattr__(
            self,
            "applicability",
            dict(
                _canonicalize(
                    self.applicability
                )
            ),
        )

        if self.exception_reference is not None:
            object.__setattr__(
                self,
                "exception_reference",
                _text(
                    self.exception_reference,
                    "exception_reference",
                ),
            )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.rule_id,
            self.version,
        )

    @property
    def effective_precedence(self) -> int:
        return (
            self.precedence
            if self.precedence is not None
            else self.priority
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "rule_id": self.rule_id,
                "version": self.version,
                "priority": self.priority,
                "precedence": (
                    self.effective_precedence
                ),
                "condition": (
                    self.condition.value
                ),
                "outcome": (
                    self.outcome.value
                ),
                "description": (
                    self.description
                ),
                "fraud_severity": (
                    self.fraud_severity.value
                    if self.fraud_severity
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
                    if self.effective_at
                    else None
                ),
                "expires_at": (
                    self.expires_at.isoformat()
                    if self.expires_at
                    else None
                ),
                "scope": self.scope,
                "applicability": (
                    self.applicability
                ),
                "exception_reference": (
                    self.exception_reference
                ),
                "provenance_reference": (
                    self.provenance_reference
                ),
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

    def applies_to(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        context = context or {}

        scope_tenant = self.scope.get(
            "tenant_id"
        )
        scope_subject = self.scope.get(
            "subject_id"
        )

        if (
            scope_tenant is not None
            and scope_tenant != tenant_id
        ):
            return False

        if (
            scope_subject is not None
            and scope_subject != subject_id
        ):
            return False

        allowed_modes = self.applicability.get(
            "operating_modes"
        )

        if allowed_modes is not None:
            if context.get(
                "operating_mode"
            ) not in set(allowed_modes):
                return False

        allowed_jurisdictions = (
            self.applicability.get(
                "jurisdictions"
            )
        )

        if allowed_jurisdictions is not None:
            if context.get(
                "jurisdiction"
            ) not in set(
                allowed_jurisdictions
            ):
                return False

        return True

    def matches(
        self,
        *,
        trust_score: TrustScore | None,
        fraud_assessment: FraudAssessment | None,
        context: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
        subject_id: str | None = None,
    ) -> bool:
        if (
            tenant_id is not None
            and subject_id is not None
            and not self.applies_to(
                tenant_id=tenant_id,
                subject_id=subject_id,
                context=context,
            )
        ):
            return False

        if (
            self.condition
            is RiskRuleCondition.FRAUD_SEVERITY
        ):
            return bool(
                fraud_assessment is not None
                and any(
                    item.severity
                    is self.fraud_severity
                    for item
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

        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "version": self.version,
            "priority": self.priority,
            "precedence": (
                self.effective_precedence
            ),
            "condition": (
                self.condition.value
            ),
            "outcome": self.outcome.value,
            "description": self.description,
            "fraud_severity": (
                self.fraud_severity.value
                if self.fraud_severity
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
                if self.effective_at
                else None
            ),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at
                else None
            ),
            "source_reference": (
                self.source_reference
            ),
            "scope": dict(self.scope),
            "applicability": dict(
                self.applicability
            ),
            "exception_reference": (
                self.exception_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class RiskRulePolicy:
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

    scope: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    applicability: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    provenance_reference: str = (
        "CORE-007.RISK_RULE_POLICY"
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
                    "Duplicate rule identity."
                )

            seen.add(rule.identity_key)

        if not isinstance(
            self.default_outcome,
            RiskRuleOutcome,
        ):
            raise RiskRuleValidationError(
                "default_outcome must be RiskRuleOutcome."
            )

        if self.effective_at is not None:
            object.__setattr__(
                self,
                "effective_at",
                _utc(
                    self.effective_at,
                    "effective_at",
                ),
            )

        if self.expires_at is not None:
            object.__setattr__(
                self,
                "expires_at",
                _utc(
                    self.expires_at,
                    "expires_at",
                ),
            )

        if (
            self.effective_at is not None
            and self.expires_at is not None
            and self.expires_at
            <= self.effective_at
        ):
            raise RiskRuleValidationError(
                "expires_at must be after effective_at."
            )

        if self.schema_version != (
            RISK_RULE_SCHEMA_VERSION
        ):
            raise RiskRuleValidationError(
                "Unsupported risk-rule schema."
            )

        object.__setattr__(
            self,
            "scope",
            dict(
                _canonicalize(
                    self.scope
                )
            ),
        )

        object.__setattr__(
            self,
            "applicability",
            dict(
                _canonicalize(
                    self.applicability
                )
            ),
        )

        object.__setattr__(
            self,
            "provenance_reference",
            _text(
                self.provenance_reference,
                "provenance_reference",
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
                    rule.fingerprint
                    for rule in self.rules
                ),
                "default_outcome": (
                    self.default_outcome.value
                ),
                "effective_at": (
                    self.effective_at.isoformat()
                    if self.effective_at
                    else None
                ),
                "expires_at": (
                    self.expires_at.isoformat()
                    if self.expires_at
                    else None
                ),
                "scope": self.scope,
                "applicability": (
                    self.applicability
                ),
                "provenance_reference": (
                    self.provenance_reference
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

        if self.fingerprint != other.fingerprint:
            raise RiskRuleConflictError(
                "Same policy identity has conflicting data."
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

    def applies_to(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        context = context or {}

        if (
            self.scope.get("tenant_id")
            not in (None, tenant_id)
        ):
            return False

        if (
            self.scope.get("subject_id")
            not in (None, subject_id)
        ):
            return False

        modes = self.applicability.get(
            "operating_modes"
        )

        if (
            modes is not None
            and context.get(
                "operating_mode"
            ) not in set(modes)
        ):
            return False

        return True

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
                if self.effective_at
                else None
            ),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at
                else None
            ),
            "scope": dict(self.scope),
            "applicability": dict(
                self.applicability
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class RiskRuleEvaluation:
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

    deterministic_evaluation_boundary: str = (
        "VERSIONED_RULES_ONLY"
    )

    reproducibility: str = (
        "DETERMINISTIC"
    )

    rule_provenance_references: tuple[str, ...] = ()

    exception_references: tuple[str, ...] = ()

    assessment_version: int = 1

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

        if (
            self.trust_score is not None
        ):
            self.trust_score = _score(
                self.trust_score,
                "trust_score",
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

        object.__setattr__(
            self,
            "evaluated_at",
            _utc(
                self.evaluated_at,
                "evaluated_at",
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
                for item in self.rule_provenance_references
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

        if (
            isinstance(
                self.assessment_version,
                bool,
            )
            or not isinstance(
                self.assessment_version,
                int,
            )
            or self.assessment_version < 1
        ):
            raise RiskRuleValidationError(
                "assessment_version must be >= 1."
            )

    @property
    def identity_key(self) -> tuple[
        str,
        str,
        str,
        str,
        int,
    ]:
        return (
            self.tenant_id,
            self.subject_id,
            self.correlation_id,
            self.policy_version,
            self.assessment_version,
        )

    @property
    def requires_review(self) -> bool:
        return self.outcome in {
            RiskRuleOutcome.REVIEW,
            RiskRuleOutcome.HIGH,
            RiskRuleOutcome.CRITICAL,
        }

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "tenant_id": self.tenant_id,
                "subject_id": self.subject_id,
                "correlation_id": (
                    self.correlation_id
                ),
                "engine_version": (
                    self.engine_version
                ),
                "policy_id": self.policy_id,
                "policy_version": (
                    self.policy_version
                ),
                "policy_fingerprint": (
                    self.policy_fingerprint
                ),
                "outcome": self.outcome.value,
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
                "deterministic_evaluation_boundary": (
                    self.deterministic_evaluation_boundary
                ),
                "reproducibility": (
                    self.reproducibility
                ),
                "rule_provenance_references": (
                    self.rule_provenance_references
                ),
                "exception_references": (
                    self.exception_references
                ),
                "assessment_version": (
                    self.assessment_version
                ),
            }
        )

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

        if self.fingerprint != other.fingerprint:
            raise RiskRuleConflictError(
                "Same risk evaluation has "
                "conflicting content."
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
            "engine_version": (
                self.engine_version
            ),
            "policy_id": self.policy_id,
            "policy_version": (
                self.policy_version
            ),
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
            "deterministic_evaluation_boundary": (
                self.deterministic_evaluation_boundary
            ),
            "reproducibility": (
                self.reproducibility
            ),
            "rule_provenance_references": list(
                self.rule_provenance_references
            ),
            "exception_references": list(
                self.exception_references
            ),
            "assessment_version": (
                self.assessment_version
            ),
            "fingerprint": self.fingerprint,
        }


class RiskRuleEngine:
    """Bounded deterministic evaluator."""

    def _validate_scope(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        trust_score: TrustScore | None,
        fraud_assessment: FraudAssessment | None,
    ) -> None:
        if trust_score is not None:
            trust_score.assert_scope(
                tenant_id=tenant_id,
                subject_id=subject_id,
            )

        if fraud_assessment is not None:
            if (
                str(fraud_assessment.tenant_id)
                != tenant_id
                or str(fraud_assessment.subject_id)
                != subject_id
            ):
                raise RiskRuleScopeError(
                    "Fraud assessment crosses "
                    "risk-rule scope."
                )

    @staticmethod
    def _evidence(
        *,
        trust_score: TrustScore | None,
        fraud_assessment: FraudAssessment | None,
    ) -> tuple[str, ...]:
        refs: set[str] = set()

        if trust_score is not None:
            refs.update(
                trust_score.signal_fingerprints
            )

        if fraud_assessment is not None:
            refs.update(
                finding_ref
                for finding in fraud_assessment.findings
                for finding_ref
                in finding.evidence_references
            )

        return tuple(sorted(refs))

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
        context: Mapping[str, Any] | None = None,
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

        if not policy.is_active(when):
            raise RiskRuleValidationError(
                "Risk-rule policy is not active."
            )

        if not policy.applies_to(
            tenant_id=tenant_id,
            subject_id=subject_id,
            context=context,
        ):
            raise RiskRuleScopeError(
                "Risk-rule policy does not apply."
            )

        self._validate_scope(
            tenant_id=tenant_id,
            subject_id=subject_id,
            trust_score=trust_score,
            fraud_assessment=fraud_assessment,
        )

        matches = [
            rule
            for rule in policy.rules
            if rule.is_active(when)
            and rule.matches(
                trust_score=trust_score,
                fraud_assessment=fraud_assessment,
                context=context,
                tenant_id=tenant_id,
                subject_id=subject_id,
            )
        ]

        matches.sort(
            key=lambda rule: (
                -_OUTCOME_RANK[
                    rule.outcome
                ],
                -rule.effective_precedence,
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
            rule_provenance_references=tuple(
                sorted(
                    {
                        item.provenance_reference
                        for item in matches
                    }
                )
            ),
            exception_references=tuple(
                sorted(
                    {
                        item.exception_reference
                        for item in matches
                        if item.exception_reference
                    }
                )
            ),
            assessment_version=1,
        )


def default_fraud_risk_policy() -> RiskRulePolicy:
    return RiskRulePolicy(
        policy_id="CORE-007-FRAUD-BASELINE",
        version="1.0",
        rules=(
            RiskRule(
                rule_id="FRAUD-SEVERITY-CRITICAL",
                version="1.0",
                priority=100,
                condition=(
                    RiskRuleCondition.FRAUD_SEVERITY
                ),
                outcome=RiskRuleOutcome.CRITICAL,
                description=(
                    "CRITICAL fraud finding maps "
                    "to CRITICAL risk."
                ),
                fraud_severity=FraudSeverity.CRITICAL,
            ),
            RiskRule(
                rule_id="FRAUD-SEVERITY-HIGH",
                version="1.0",
                priority=90,
                condition=(
                    RiskRuleCondition.FRAUD_SEVERITY
                ),
                outcome=RiskRuleOutcome.HIGH,
                description=(
                    "HIGH fraud finding maps "
                    "to HIGH risk."
                ),
                fraud_severity=FraudSeverity.HIGH,
            ),
            RiskRule(
                rule_id="FRAUD-SEVERITY-REVIEW",
                version="1.0",
                priority=80,
                condition=(
                    RiskRuleCondition.FRAUD_SEVERITY
                ),
                outcome=RiskRuleOutcome.REVIEW,
                description=(
                    "REVIEW fraud finding maps "
                    "to REVIEW risk."
                ),
                fraud_severity=FraudSeverity.REVIEW,
            ),
            RiskRule(
                rule_id="FRAUD-TRIPWIRE",
                version="1.0",
                priority=70,
                condition=(
                    RiskRuleCondition.FRAUD_TRIPWIRE
                ),
                outcome=RiskRuleOutcome.HIGH,
                description=(
                    "Fraud tripwire requires "
                    "HIGH risk classification."
                ),
            ),
        ),
        provenance_reference=(
            "CORE-007.RISK_RULE.BASELINE"
        ),
    )


__all__ = [
    "RISK_RULE_SCHEMA_VERSION",
    "RISK_RULE_ENGINE_VERSION",
    "RiskRuleError",
    "RiskRuleValidationError",
    "RiskRuleScopeError",
    "RiskRuleConflictError",
    "RiskRuleOutcome",
    "RiskRuleCondition",
    "RiskRule",
    "RiskRulePolicy",
    "RiskRuleEvaluation",
    "RiskRuleEngine",
    "default_fraud_risk_policy",
]
