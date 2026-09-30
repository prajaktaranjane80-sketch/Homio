from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID
import hashlib
import json


RISK_ASSESSMENT_SCHEMA_VERSION = 1
RISK_ASSESSMENT_MODEL_VERSION = "1.0"
RISK_SCORE_MIN = 0
RISK_SCORE_MAX = 100


class RiskAssessmentError(ValueError):
    """Base CORE-007 risk assessment error."""


class RiskAssessmentValidationError(
    RiskAssessmentError
):
    """Invalid risk assessment contract."""


class RiskAssessmentScopeError(
    RiskAssessmentError
):
    """Tenant or subject boundary violation."""


class RiskAssessmentConflictError(
    RiskAssessmentError
):
    """Conflicting risk assessment identity."""


class RiskAssessmentInsufficientEvidenceError(
    RiskAssessmentError
):
    """Insufficient evidence."""


class RiskLevel(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        return {
            RiskLevel.INFORMATIONAL: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4,
        }[self]


class RiskFactorSource(str, Enum):
    TRUST_SCORE = "TRUST_SCORE"
    FRAUD_FINDING = "FRAUD_FINDING"
    FRAUD_ASSESSMENT = "FRAUD_ASSESSMENT"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RiskAssessmentValidationError(
            f"{field_name} must be non-empty text."
        )

    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise RiskAssessmentValidationError(
            f"{field_name} must be integer >= 1."
        )
    return value


def _bounded_score(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < RISK_SCORE_MIN
        or value > RISK_SCORE_MAX
    ):
        raise RiskAssessmentValidationError(
            f"{field_name} must be between "
            f"{RISK_SCORE_MIN} and {RISK_SCORE_MAX}."
        )
    return value


def _non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise RiskAssessmentValidationError(
            f"{field_name} must be integer >= 0."
        )
    return value


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise RiskAssessmentValidationError(
            f"{field_name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise RiskAssessmentValidationError(
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

    raise RiskAssessmentValidationError(
        "Unsupported canonical value type: "
        f"{type(value).__name__}"
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
class RiskFactor:
    """Immutable evidence-linked risk factor."""

    factor_id: str
    source_type: RiskFactorSource
    code: str
    raw_value: str
    contribution_points: int
    evidence_references: tuple[str, ...]
    source_references: tuple[str, ...]
    source_fingerprint: str
    observed_at: datetime

    provenance_reference: str = (
        "CORE-007.RISK_FACTOR"
    )

    def __post_init__(self) -> None:
        for name in (
            "factor_id",
            "code",
            "raw_value",
            "source_fingerprint",
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

        if not isinstance(
            self.source_type,
            RiskFactorSource,
        ):
            raise RiskAssessmentValidationError(
                "source_type must be RiskFactorSource."
            )

        object.__setattr__(
            self,
            "contribution_points",
            _non_negative_int(
                self.contribution_points,
                "contribution_points",
            ),
        )

        evidence = tuple(
            _text(
                item,
                "evidence_reference",
            )
            for item in self.evidence_references
        )

        sources = tuple(
            _text(
                item,
                "source_reference",
            )
            for item in self.source_references
        )

        if not evidence and not sources:
            raise RiskAssessmentInsufficientEvidenceError(
                "Risk factor requires evidence or sources."
            )

        object.__setattr__(
            self,
            "evidence_references",
            evidence,
        )

        object.__setattr__(
            self,
            "source_references",
            sources,
        )

        object.__setattr__(
            self,
            "observed_at",
            _utc(
                self.observed_at,
                "observed_at",
            ),
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "factor_id": self.factor_id,
                "source_type": (
                    self.source_type.value
                ),
                "code": self.code,
                "raw_value": self.raw_value,
                "contribution_points": (
                    self.contribution_points
                ),
                "evidence_references": (
                    self.evidence_references
                ),
                "source_references": (
                    self.source_references
                ),
                "source_fingerprint": (
                    self.source_fingerprint
                ),
                "observed_at": (
                    self.observed_at.isoformat()
                ),
                "provenance_reference": (
                    self.provenance_reference
                ),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "source_type": (
                self.source_type.value
            ),
            "code": self.code,
            "raw_value": self.raw_value,
            "contribution_points": (
                self.contribution_points
            ),
            "evidence_references": list(
                self.evidence_references
            ),
            "source_references": list(
                self.source_references
            ),
            "source_fingerprint": (
                self.source_fingerprint
            ),
            "observed_at": (
                self.observed_at.isoformat()
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class RiskEvaluationTrace:
    """Deterministic explanation of one evaluation step."""

    factor_id: str
    rule_reference: str
    input_reference: str
    contribution_points: int
    resulting_level: RiskLevel
    explanation: str

    def __post_init__(self) -> None:
        for name in (
            "factor_id",
            "rule_reference",
            "input_reference",
            "explanation",
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
            self.resulting_level,
            RiskLevel,
        ):
            raise RiskAssessmentValidationError(
                "resulting_level must be RiskLevel."
            )

        object.__setattr__(
            self,
            "contribution_points",
            _non_negative_int(
                self.contribution_points,
                "contribution_points",
            ),
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "factor_id": self.factor_id,
                "rule_reference": (
                    self.rule_reference
                ),
                "input_reference": (
                    self.input_reference
                ),
                "contribution_points": (
                    self.contribution_points
                ),
                "resulting_level": (
                    self.resulting_level.value
                ),
                "explanation": self.explanation,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "rule_reference": (
                self.rule_reference
            ),
            "input_reference": (
                self.input_reference
            ),
            "contribution_points": (
                self.contribution_points
            ),
            "resulting_level": (
                self.resulting_level.value
            ),
            "explanation": self.explanation,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """
    Immutable deterministic risk assessment.

    Explicit:
    - risk subject
    - risk context
    - risk factors
    - evidence
    - assessment version
    - assessment history
    - reproducibility
    """

    assessment_id: UUID
    tenant_id: str
    subject_id: str

    assessment_version: int

    risk_score: int
    risk_level: RiskLevel

    policy_version: str
    policy_fingerprint: str

    factors: tuple[RiskFactor, ...]
    evaluation_trace: tuple[
        RiskEvaluationTrace,
        ...
    ]

    input_fingerprints: tuple[str, ...]

    evaluated_at: datetime

    schema_version: int = (
        RISK_ASSESSMENT_SCHEMA_VERSION
    )

    model_version: str = (
        RISK_ASSESSMENT_MODEL_VERSION
    )

    source_of_truth: str = (
        "risk_assessment"
    )

    risk_context: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    assessment_history: tuple[str, ...] = ()

    assessment_explanation: str = (
        "Deterministic CORE-007 risk assessment."
    )

    reproducibility: str = (
        "DETERMINISTIC"
    )

    provenance_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
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

        if not isinstance(
            self.assessment_id,
            UUID,
        ):
            raise RiskAssessmentValidationError(
                "assessment_id must be UUID."
            )

        object.__setattr__(
            self,
            "assessment_version",
            _positive_int(
                self.assessment_version,
                "assessment_version",
            ),
        )

        object.__setattr__(
            self,
            "risk_score",
            _bounded_score(
                self.risk_score,
                "risk_score",
            ),
        )

        if not isinstance(
            self.risk_level,
            RiskLevel,
        ):
            raise RiskAssessmentValidationError(
                "risk_level must be RiskLevel."
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

        if not self.factors:
            raise RiskAssessmentInsufficientEvidenceError(
                "Risk assessment requires factors."
            )

        factor_ids = tuple(
            item.factor_id
            for item in self.factors
        )

        if len(factor_ids) != len(
            set(factor_ids)
        ):
            raise RiskAssessmentConflictError(
                "Duplicate factor identity."
            )

        if not all(
            isinstance(
                item,
                RiskFactor,
            )
            for item in self.factors
        ):
            raise RiskAssessmentValidationError(
                "Invalid RiskFactor."
            )

        if not isinstance(
            self.evaluation_trace,
            tuple,
        ):
            raise RiskAssessmentValidationError(
                "evaluation_trace must be tuple."
            )

        trace_ids = tuple(
            item.factor_id
            for item in self.evaluation_trace
        )

        if set(trace_ids) != set(factor_ids):
            raise RiskAssessmentValidationError(
                "Trace must cover every risk factor."
            )

        if len(trace_ids) != len(
            set(trace_ids)
        ):
            raise RiskAssessmentConflictError(
                "Duplicate trace factor."
            )

        if not self.input_fingerprints:
            raise RiskAssessmentInsufficientEvidenceError(
                "Input fingerprints required."
            )

        object.__setattr__(
            self,
            "input_fingerprints",
            tuple(
                sorted(
                    {
                        _text(
                            item,
                            "input_fingerprint",
                        )
                        for item in self.input_fingerprints
                    }
                )
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

        if self.schema_version != (
            RISK_ASSESSMENT_SCHEMA_VERSION
        ):
            raise RiskAssessmentValidationError(
                "Unsupported assessment schema."
            )

        object.__setattr__(
            self,
            "model_version",
            _text(
                self.model_version,
                "model_version",
            ),
        )

        if self.source_of_truth != (
            "risk_assessment"
        ):
            raise RiskAssessmentValidationError(
                "source_of_truth must be risk_assessment."
            )

        if not isinstance(
            self.risk_context,
            Mapping,
        ):
            raise RiskAssessmentValidationError(
                "risk_context must be mapping."
            )

        object.__setattr__(
            self,
            "risk_context",
            MappingProxyType(
                _canonicalize(
                    dict(self.risk_context)
                )
            ),
        )

        object.__setattr__(
            self,
            "assessment_history",
            tuple(
                _text(
                    item,
                    "assessment_history",
                )
                for item in self.assessment_history
            ),
        )

        object.__setattr__(
            self,
            "assessment_explanation",
            _text(
                self.assessment_explanation,
                "assessment_explanation",
            ),
        )

        object.__setattr__(
            self,
            "reproducibility",
            _text(
                self.reproducibility,
                "reproducibility",
            ),
        )

        object.__setattr__(
            self,
            "provenance_references",
            tuple(
                _text(
                    item,
                    "provenance_reference",
                )
                for item in self.provenance_references
            ),
        )

    @property
    def subject_key(self) -> tuple[str, str]:
        return (
            self.tenant_id,
            self.subject_id,
        )

    @property
    def determinism_key(self) -> str:
        return _fingerprint(
            {
                "tenant_id": self.tenant_id,
                "subject_id": self.subject_id,
                "assessment_version": (
                    self.assessment_version
                ),
                "policy_version": (
                    self.policy_version
                ),
                "policy_fingerprint": (
                    self.policy_fingerprint
                ),
                "risk_context": dict(
                    self.risk_context
                ),
                "factors": tuple(
                    item.fingerprint
                    for item in self.factors
                ),
            }
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "tenant_id": self.tenant_id,
                "subject_id": self.subject_id,
                "assessment_version": (
                    self.assessment_version
                ),
                "risk_score": self.risk_score,
                "risk_level": (
                    self.risk_level.value
                ),
                "policy_version": (
                    self.policy_version
                ),
                "policy_fingerprint": (
                    self.policy_fingerprint
                ),
                "risk_context": dict(
                    self.risk_context
                ),
                "factors": tuple(
                    item.fingerprint
                    for item in self.factors
                ),
                "evaluation_trace": tuple(
                    item.fingerprint
                    for item in self.evaluation_trace
                ),
                "input_fingerprints": (
                    self.input_fingerprints
                ),
                "assessment_history": (
                    self.assessment_history
                ),
                "assessment_explanation": (
                    self.assessment_explanation
                ),
                "reproducibility": (
                    self.reproducibility
                ),
                "provenance_references": (
                    self.provenance_references
                ),
                "schema_version": (
                    self.schema_version
                ),
                "model_version": (
                    self.model_version
                ),
                "source_of_truth": (
                    self.source_of_truth
                ),
            }
        )

    def assert_scope(
        self,
        *,
        tenant_id: str,
        subject_id: str,
    ) -> None:
        if (
            self.tenant_id != _text(
                tenant_id,
                "tenant_id",
            )
            or self.subject_id != _text(
                subject_id,
                "subject_id",
            )
        ):
            raise RiskAssessmentScopeError(
                "Risk assessment crosses tenant "
                "or subject scope."
            )

    def assert_compatible(
        self,
        other: "RiskAssessment",
    ) -> None:
        if not isinstance(
            other,
            RiskAssessment,
        ):
            raise RiskAssessmentValidationError(
                "other must be RiskAssessment."
            )

        if (
            self.determinism_key
            != other.determinism_key
        ):
            raise RiskAssessmentConflictError(
                "Risk assessment deterministic "
                "identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise RiskAssessmentConflictError(
                "Same risk assessment identity "
                "has conflicting content."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": str(
                self.assessment_id
            ),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "assessment_version": (
                self.assessment_version
            ),
            "risk_score": self.risk_score,
            "risk_level": (
                self.risk_level.value
            ),
            "policy_version": (
                self.policy_version
            ),
            "policy_fingerprint": (
                self.policy_fingerprint
            ),
            "risk_context": dict(
                self.risk_context
            ),
            "factors": [
                item.to_dict()
                for item in self.factors
            ],
            "evaluation_trace": [
                item.to_dict()
                for item in self.evaluation_trace
            ],
            "input_fingerprints": list(
                self.input_fingerprints
            ),
            "evaluated_at": (
                self.evaluated_at.isoformat()
            ),
            "schema_version": (
                self.schema_version
            ),
            "model_version": (
                self.model_version
            ),
            "source_of_truth": (
                self.source_of_truth
            ),
            "assessment_history": list(
                self.assessment_history
            ),
            "assessment_explanation": (
                self.assessment_explanation
            ),
            "reproducibility": (
                self.reproducibility
            ),
            "provenance_references": list(
                self.provenance_references
            ),
            "determinism_key": (
                self.determinism_key
            ),
            "fingerprint": self.fingerprint,
        }


__all__ = [
    "RISK_ASSESSMENT_SCHEMA_VERSION",
    "RISK_ASSESSMENT_MODEL_VERSION",
    "RISK_SCORE_MIN",
    "RISK_SCORE_MAX",
    "RiskAssessmentError",
    "RiskAssessmentValidationError",
    "RiskAssessmentScopeError",
    "RiskAssessmentConflictError",
    "RiskAssessmentInsufficientEvidenceError",
    "RiskLevel",
    "RiskFactorSource",
    "RiskFactor",
    "RiskEvaluationTrace",
    "RiskAssessment",
]
