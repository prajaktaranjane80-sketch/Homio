from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping


TRUST_SCORE_SCHEMA_VERSION = 1
TRUST_SCORE_MODEL_VERSION = "1.0"
TRUST_SCORE_MIN = 0
TRUST_SCORE_MAX = 100


class TrustScoreError(ValueError):
    """Base Trust Score foundation error."""


class TrustScoreValidationError(TrustScoreError):
    """Invalid Trust Score contract data."""


class TrustScoreScopeError(TrustScoreError):
    """Tenant or subject boundary violation."""


class TrustScoreConflictError(TrustScoreError):
    """Conflicting Trust Score identity or signal."""


class TrustScoreInsufficientEvidenceError(TrustScoreError):
    """Trust Score cannot be computed from the supplied evidence."""


class TrustScoreDecisionBoundary(str, Enum):
    """
    T01 deliberately contains no allow/deny or fraud decision.

    Trust score is a measured trust signal. Risk, fraud and governance
    authorities consume it later through their own approved boundaries.
    """

    INFORMATIONAL = "INFORMATIONAL"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrustScoreValidationError(
            f"{field_name} must be non-empty text."
        )

    return value.strip()


def _positive_int(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise TrustScoreValidationError(
            f"{field_name} must be an integer >= 1."
        )

    return value


def _percentage(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < TRUST_SCORE_MIN
        or value > TRUST_SCORE_MAX
    ):
        raise TrustScoreValidationError(
            f"{field_name} must be an integer between "
            f"{TRUST_SCORE_MIN} and {TRUST_SCORE_MAX}."
        )

    return value


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TrustScoreValidationError(
            f"{field_name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise TrustScoreValidationError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

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

    raise TrustScoreValidationError(
        "Unsupported value type: "
        f"{type(value).__name__}"
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class TrustScoringModel:
    """
    Versioned, immutable scoring model.

    The model owns category weighting. Callers cannot silently inject
    arbitrary weights into a signal. Governance/approval of models belongs
    to later CORE-007 governance work.
    """

    model_version: str
    category_weights_bps: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "model_version",
            _text(
                self.model_version,
                "model_version",
            ),
        )

        if not isinstance(
            self.category_weights_bps,
            Mapping,
        ):
            raise TrustScoreValidationError(
                "category_weights_bps must be a mapping."
            )

        normalized: dict[str, int] = {}

        for category, weight in (
            self.category_weights_bps.items()
        ):
            normalized_category = _text(
                category,
                "category",
            )

            if normalized_category in normalized:
                raise TrustScoreConflictError(
                    "Duplicate normalized scoring category."
                )

            if (
                isinstance(weight, bool)
                or not isinstance(weight, int)
                or weight < 1
                or weight > 10000
            ):
                raise TrustScoreValidationError(
                    "Each category weight must be an integer "
                    "between 1 and 10000."
                )

            normalized[
                normalized_category
            ] = weight

        if not normalized:
            raise TrustScoreInsufficientEvidenceError(
                "Scoring model requires at least one category."
            )

        object.__setattr__(
            self,
            "category_weights_bps",
            MappingProxyType(normalized),
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "model_version": self.model_version,
                "category_weights_bps": dict(
                    self.category_weights_bps
                ),
            }
        )

    def weight_for(
        self,
        category: str,
    ) -> int:
        category = _text(
            category,
            "category",
        )

        try:
            return self.category_weights_bps[category]
        except KeyError as exc:
            raise TrustScoreInsufficientEvidenceError(
                f"No scoring weight configured for category "
                f"{category!r}."
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "category_weights_bps": dict(
                self.category_weights_bps
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class TrustSignal:
    """
    Immutable observed trust evidence.

    This is NOT:
    - a fraud verdict
    - a risk decision
    - a governance decision
    - an authorization decision
    """

    signal_id: str
    tenant_id: str
    subject_id: str
    category: str
    value: int
    evidence_reference: str
    source_reference: str
    observed_at: datetime
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )
    schema_version: int = TRUST_SCORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "signal_id",
            "tenant_id",
            "subject_id",
            "category",
            "evidence_reference",
            "source_reference",
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
            "value",
            _percentage(
                self.value,
                "value",
            ),
        )

        object.__setattr__(
            self,
            "observed_at",
            _utc(
                self.observed_at,
                "observed_at",
            ),
        )

        if self.schema_version != TRUST_SCORE_SCHEMA_VERSION:
            raise TrustScoreValidationError(
                "Unsupported Trust Score schema version."
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TrustScoreValidationError(
                "metadata must be a mapping."
            )

        normalized = _canonicalize(
            dict(self.metadata)
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(normalized),
        )

    @property
    def identity_key(self) -> tuple[str, str, str]:
        return (
            self.tenant_id,
            self.subject_id,
            self.signal_id,
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "signal_id": self.signal_id,
                "tenant_id": self.tenant_id,
                "subject_id": self.subject_id,
                "category": self.category,
                "value": self.value,
                "evidence_reference": (
                    self.evidence_reference
                ),
                "source_reference": (
                    self.source_reference
                ),
                "observed_at": (
                    self.observed_at.isoformat()
                ),
                "metadata": dict(self.metadata),
                "schema_version": self.schema_version,
            }
        )

    def assert_scope(
        self,
        *,
        tenant_id: str,
        subject_id: str,
    ) -> None:
        if (
            self.tenant_id != tenant_id
            or self.subject_id != subject_id
        ):
            raise TrustScoreScopeError(
                "Trust signal crosses tenant or subject scope."
            )

    def assert_compatible(
        self,
        other: "TrustSignal",
    ) -> None:
        if not isinstance(
            other,
            TrustSignal,
        ):
            raise TrustScoreValidationError(
                "other must be TrustSignal."
            )

        if self.identity_key != other.identity_key:
            raise TrustScoreConflictError(
                "Trust signal identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise TrustScoreConflictError(
                "Same Trust signal identity has conflicting data."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "category": self.category,
            "value": self.value,
            "evidence_reference": (
                self.evidence_reference
            ),
            "source_reference": (
                self.source_reference
            ),
            "observed_at": (
                self.observed_at.isoformat()
            ),
            "metadata": dict(self.metadata),
            "schema_version": self.schema_version,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class TrustScoreContribution:
    signal_id: str
    category: str
    value: int
    weight_bps: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "signal_id",
            _text(
                self.signal_id,
                "signal_id",
            ),
        )
        object.__setattr__(
            self,
            "category",
            _text(
                self.category,
                "category",
            ),
        )
        object.__setattr__(
            self,
            "value",
            _percentage(
                self.value,
                "value",
            ),
        )

        if (
            isinstance(self.weight_bps, bool)
            or not isinstance(
                self.weight_bps,
                int,
            )
            or self.weight_bps < 1
        ):
            raise TrustScoreValidationError(
                "weight_bps must be an integer >= 1."
            )

    @property
    def weighted_value(self) -> int:
        return self.value * self.weight_bps

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "category": self.category,
            "value": self.value,
            "weight_bps": self.weight_bps,
            "weighted_value": self.weighted_value,
        }


@dataclass(frozen=True, slots=True)
class TrustScore:
    """
    Immutable, evidence-linked trust score.

    TrustScore is descriptive intelligence. It is deliberately not an
    authorization, fraud or governance verdict.
    """

    tenant_id: str
    subject_id: str
    score: int
    model_version: str
    model_fingerprint: str
    signal_ids: tuple[str, ...]
    signal_fingerprints: tuple[str, ...]
    contributions: tuple[
        TrustScoreContribution,
        ...
    ]
    total_weight_bps: int
    computed_at: datetime
    schema_version: int = TRUST_SCORE_SCHEMA_VERSION
    source_of_truth: str = "trust_score"

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "subject_id",
            "model_version",
            "model_fingerprint",
            "source_of_truth",
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
            "score",
            _percentage(
                self.score,
                "score",
            ),
        )

        if not self.signal_ids:
            raise TrustScoreInsufficientEvidenceError(
                "TrustScore requires at least one signal."
            )

        if len(self.signal_ids) != len(
            self.signal_fingerprints
        ):
            raise TrustScoreValidationError(
                "Signal identity and fingerprint lengths differ."
            )

        if len(self.signal_ids) != len(
            self.contributions
        ):
            raise TrustScoreValidationError(
                "Signal identity and contribution lengths differ."
            )

        object.__setattr__(
            self,
            "signal_ids",
            tuple(
                _text(signal_id, "signal_id")
                for signal_id in self.signal_ids
            ),
        )

        object.__setattr__(
            self,
            "signal_fingerprints",
            tuple(
                _text(
                    fingerprint,
                    "signal_fingerprint",
                )
                for fingerprint
                in self.signal_fingerprints
            ),
        )

        object.__setattr__(
            self,
            "total_weight_bps",
            _positive_int(
                self.total_weight_bps,
                "total_weight_bps",
            ),
        )

        object.__setattr__(
            self,
            "computed_at",
            _utc(
                self.computed_at,
                "computed_at",
            ),
        )

        if self.schema_version != TRUST_SCORE_SCHEMA_VERSION:
            raise TrustScoreValidationError(
                "Unsupported TrustScore schema version."
            )

    @property
    def subject_key(self) -> tuple[str, str]:
        return (
            self.tenant_id,
            self.subject_id,
        )

    @property
    def evidence_count(self) -> int:
        return len(self.signal_ids)

    @property
    def identity_key(self) -> tuple[
        str,
        str,
        str,
        tuple[str, ...],
    ]:
        return (
            self.tenant_id,
            self.subject_id,
            self.model_version,
            self.signal_ids,
        )

    def assert_scope(
        self,
        *,
        tenant_id: str,
        subject_id: str,
    ) -> None:
        if (
            self.tenant_id != tenant_id
            or self.subject_id != subject_id
        ):
            raise TrustScoreScopeError(
                "Trust score crosses tenant or subject scope."
            )

    def assert_compatible(
        self,
        other: "TrustScore",
    ) -> None:
        if not isinstance(
            other,
            TrustScore,
        ):
            raise TrustScoreValidationError(
                "other must be TrustScore."
            )

        if self.identity_key != other.identity_key:
            raise TrustScoreConflictError(
                "Trust score identities differ."
            )

        if self.to_dict() != other.to_dict():
            raise TrustScoreConflictError(
                "Same Trust score identity has conflicting data."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "score": self.score,
            "model_version": self.model_version,
            "model_fingerprint": self.model_fingerprint,
            "signal_ids": list(self.signal_ids),
            "signal_fingerprints": list(
                self.signal_fingerprints
            ),
            "contributions": [
                item.to_dict()
                for item in self.contributions
            ],
            "total_weight_bps": self.total_weight_bps,
            "computed_at": (
                self.computed_at.isoformat()
            ),
            "schema_version": self.schema_version,
            "source_of_truth": self.source_of_truth,
            "evidence_count": self.evidence_count,
        }


class TrustScoreEngine:
    """
    CORE-007 / ARCH-015 trust-score computation authority.

    Explicitly excluded:
    - fraud detection
    - risk policy decisions
    - governance policy evaluation
    - authorization
    - approval workflows
    - event transport
    - Control Center state
    """

    MODEL_VERSION = TRUST_SCORE_MODEL_VERSION

    @classmethod
    def compute(
        cls,
        *,
        tenant_id: str,
        subject_id: str,
        signals: tuple[TrustSignal, ...] | list[TrustSignal],
        model: TrustScoringModel,
        computed_at: datetime,
    ) -> TrustScore:
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )
        subject_id = _text(
            subject_id,
            "subject_id",
        )

        if not isinstance(
            model,
            TrustScoringModel,
        ):
            raise TrustScoreValidationError(
                "model must be TrustScoringModel."
            )

        normalized_signals = tuple(signals)

        if not normalized_signals:
            raise TrustScoreInsufficientEvidenceError(
                "Trust score requires at least one signal."
            )

        by_id: dict[str, TrustSignal] = {}

        for signal in normalized_signals:
            if not isinstance(
                signal,
                TrustSignal,
            ):
                raise TrustScoreValidationError(
                    "All signals must be TrustSignal instances."
                )

            signal.assert_scope(
                tenant_id=tenant_id,
                subject_id=subject_id,
            )

            existing = by_id.get(
                signal.signal_id
            )

            if existing is not None:
                existing.assert_compatible(signal)
                raise TrustScoreConflictError(
                    "Duplicate signal identity supplied."
                )

            by_id[signal.signal_id] = signal

        ordered_signals = tuple(
            by_id[key]
            for key in sorted(by_id)
        )

        contributions: list[
            TrustScoreContribution
        ] = []

        numerator = Decimal(0)
        total_weight = 0

        for signal in ordered_signals:
            weight = model.weight_for(
                signal.category
            )

            contribution = TrustScoreContribution(
                signal_id=signal.signal_id,
                category=signal.category,
                value=signal.value,
                weight_bps=weight,
            )

            contributions.append(
                contribution
            )

            numerator += (
                Decimal(signal.value)
                * Decimal(weight)
            )
            total_weight += weight

        if total_weight <= 0:
            raise TrustScoreInsufficientEvidenceError(
                "Total scoring weight must be greater than zero."
            )

        score = int(
            (
                numerator
                / Decimal(total_weight)
            ).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )

        return TrustScore(
            tenant_id=tenant_id,
            subject_id=subject_id,
            score=score,
            model_version=model.model_version,
            model_fingerprint=model.fingerprint,
            signal_ids=tuple(
                signal.signal_id
                for signal in ordered_signals
            ),
            signal_fingerprints=tuple(
                signal.fingerprint
                for signal in ordered_signals
            ),
            contributions=tuple(
                contributions
            ),
            total_weight_bps=total_weight,
            computed_at=_utc(
                computed_at,
                "computed_at",
            ),
        )


__all__ = [
    "TRUST_SCORE_SCHEMA_VERSION",
    "TRUST_SCORE_MODEL_VERSION",
    "TRUST_SCORE_MIN",
    "TRUST_SCORE_MAX",
    "TrustScoreError",
    "TrustScoreValidationError",
    "TrustScoreScopeError",
    "TrustScoreConflictError",
    "TrustScoreInsufficientEvidenceError",
    "TrustScoreDecisionBoundary",
    "TrustScoringModel",
    "TrustSignal",
    "TrustScoreContribution",
    "TrustScore",
    "TrustScoreEngine",
]