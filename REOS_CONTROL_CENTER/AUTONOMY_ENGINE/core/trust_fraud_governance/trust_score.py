from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import hashlib
import json


TRUST_SCORE_SCHEMA_VERSION = 1
TRUST_SCORE_MODEL_VERSION = "1.0"
TRUST_SCORE_MIN = 0
TRUST_SCORE_MAX = 100


class TrustScoreError(ValueError):
    """Base CORE-007 trust-score error."""


class TrustScoreValidationError(TrustScoreError):
    """Invalid trust contract data."""


class TrustScoreScopeError(TrustScoreError):
    """Tenant or subject boundary violation."""


class TrustScoreConflictError(TrustScoreError):
    """Conflicting trust identity or evidence."""


class TrustScoreInsufficientEvidenceError(TrustScoreError):
    """Insufficient evidence for trust calculation."""


class TrustState(str, Enum):
    OBSERVED = "OBSERVED"
    ACTIVE = "ACTIVE"
    REVIEW = "REVIEW"
    HISTORICAL = "HISTORICAL"


class TrustScoreDecisionBoundary(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrustScoreValidationError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise TrustScoreValidationError(
            f"{field_name} must be an integer >= 1."
        )
    return value


def _percentage(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < TRUST_SCORE_MIN
        or value > TRUST_SCORE_MAX
    ):
        raise TrustScoreValidationError(
            f"{field_name} must be between "
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
        isinstance(value, (str, int, float, bool))
        or value is None
    ):
        return value

    raise TrustScoreValidationError(
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
class TrustScoringModel:
    """Versioned immutable trust scoring model."""

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
            category = _text(
                category,
                "category",
            )

            if (
                isinstance(weight, bool)
                or not isinstance(weight, int)
                or weight < 1
                or weight > 10000
            ):
                raise TrustScoreValidationError(
                    "Each category weight must be "
                    "between 1 and 10000."
                )

            if category in normalized:
                raise TrustScoreConflictError(
                    "Duplicate trust category."
                )

            normalized[category] = weight

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

    def weight_for(self, category: str) -> int:
        category = _text(
            category,
            "category",
        )

        try:
            return self.category_weights_bps[
                category
            ]
        except KeyError as exc:
            raise TrustScoreInsufficientEvidenceError(
                f"No scoring weight configured for "
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
    Immutable CORE-007 trust signal.

    Explicitly carries:
    - subject identity
    - tenant identity
    - trust context
    - signal provenance
    - confidence metadata
    - signal version
    - trust state
    - historical linkage

    It is never an authorization or fraud verdict.
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

    context: Mapping[str, Any] = field(
        default_factory=dict
    )

    provenance_reference: str = (
        "CORE-007.TRUST_SIGNAL"
    )

    confidence_metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    signal_version: int = 1

    trust_state: TrustState = (
        TrustState.OBSERVED
    )

    history_reference: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "signal_id",
            "tenant_id",
            "subject_id",
            "category",
            "evidence_reference",
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

        if self.schema_version != (
            TRUST_SCORE_SCHEMA_VERSION
        ):
            raise TrustScoreValidationError(
                "Unsupported trust-score schema."
            )

        object.__setattr__(
            self,
            "signal_version",
            _positive_int(
                self.signal_version,
                "signal_version",
            ),
        )

        if not isinstance(
            self.trust_state,
            TrustState,
        ):
            raise TrustScoreValidationError(
                "trust_state must be TrustState."
            )

        if not isinstance(
            self.context,
            Mapping,
        ):
            raise TrustScoreValidationError(
                "context must be mapping."
            )

        if not isinstance(
            self.confidence_metadata,
            Mapping,
        ):
            raise TrustScoreValidationError(
                "confidence_metadata must be mapping."
            )

        object.__setattr__(
            self,
            "context",
            MappingProxyType(
                _canonicalize(
                    dict(self.context)
                )
            ),
        )

        object.__setattr__(
            self,
            "confidence_metadata",
            MappingProxyType(
                _canonicalize(
                    dict(self.confidence_metadata)
                )
            ),
        )

        if self.history_reference is not None:
            object.__setattr__(
                self,
                "history_reference",
                _text(
                    self.history_reference,
                    "history_reference",
                ),
            )

    @property
    def trust_context(self) -> Mapping[str, Any]:
        return self.context

    @property
    def provenance(self) -> str:
        return self.provenance_reference

    @property
    def confidence(self) -> Mapping[str, Any]:
        return self.confidence_metadata

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
                "metadata": dict(
                    self.metadata
                ),
                "schema_version": (
                    self.schema_version
                ),
                "context": dict(
                    self.context
                ),
                "provenance_reference": (
                    self.provenance_reference
                ),
                "confidence_metadata": dict(
                    self.confidence_metadata
                ),
                "signal_version": (
                    self.signal_version
                ),
                "trust_state": (
                    self.trust_state.value
                ),
                "history_reference": (
                    self.history_reference
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
            self.tenant_id != tenant_id
            or self.subject_id != subject_id
        ):
            raise TrustScoreScopeError(
                "Trust signal crosses tenant or "
                "subject scope."
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

        if (
            self.identity_key
            != other.identity_key
        ):
            raise TrustScoreConflictError(
                "Trust signal identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise TrustScoreConflictError(
                "Same signal identity has conflicting data."
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
            "context": dict(self.context),
            "provenance_reference": (
                self.provenance_reference
            ),
            "confidence_metadata": dict(
                self.confidence_metadata
            ),
            "signal_version": self.signal_version,
            "trust_state": self.trust_state.value,
            "history_reference": (
                self.history_reference
            ),
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
                "weight_bps must be >= 1."
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
    Immutable trust score with explicit history/version/provenance.

    This remains descriptive intelligence only.
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

    trust_state: TrustState = TrustState.ACTIVE
    trust_version: int = 1
    trust_history: tuple[str, ...] = ()
    provenance_references: tuple[str, ...] = ()
    confidence_metadata: Mapping[str, Any] = (
        field(default_factory=dict)
    )

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
                "Signal identity/fingerprint counts differ."
            )

        if len(self.signal_ids) != len(
            self.contributions
        ):
            raise TrustScoreValidationError(
                "Signal/contribution counts differ."
            )

        object.__setattr__(
            self,
            "signal_ids",
            tuple(
                _text(
                    value,
                    "signal_id",
                )
                for value in self.signal_ids
            ),
        )

        object.__setattr__(
            self,
            "signal_fingerprints",
            tuple(
                _text(
                    value,
                    "signal_fingerprint",
                )
                for value in self.signal_fingerprints
            ),
        )

        if len(self.signal_ids) != len(
            set(self.signal_ids)
        ):
            raise TrustScoreConflictError(
                "Duplicate signal identities."
            )

        if not all(
            isinstance(
                item,
                TrustScoreContribution,
            )
            for item in self.contributions
        ):
            raise TrustScoreValidationError(
                "Invalid TrustScore contribution."
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

        if self.schema_version != (
            TRUST_SCORE_SCHEMA_VERSION
        ):
            raise TrustScoreValidationError(
                "Unsupported TrustScore schema."
            )

        if not isinstance(
            self.trust_state,
            TrustState,
        ):
            raise TrustScoreValidationError(
                "trust_state must be TrustState."
            )

        object.__setattr__(
            self,
            "trust_version",
            _positive_int(
                self.trust_version,
                "trust_version",
            ),
        )

        object.__setattr__(
            self,
            "trust_history",
            tuple(
                _text(
                    item,
                    "trust_history_reference",
                )
                for item in self.trust_history
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

        if not isinstance(
            self.confidence_metadata,
            Mapping,
        ):
            raise TrustScoreValidationError(
                "confidence_metadata must be mapping."
            )

        object.__setattr__(
            self,
            "confidence_metadata",
            MappingProxyType(
                _canonicalize(
                    dict(
                        self.confidence_metadata
                    )
                )
            ),
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
    def trust_history(self) -> tuple[str, ...]:
        return self.__dict__["trust_history"]

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
                "Trust score crosses tenant or "
                "subject scope."
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
                "Same trust-score identity has "
                "conflicting data."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "score": self.score,
            "model_version": self.model_version,
            "model_fingerprint": (
                self.model_fingerprint
            ),
            "signal_ids": list(self.signal_ids),
            "signal_fingerprints": list(
                self.signal_fingerprints
            ),
            "contributions": [
                item.to_dict()
                for item in self.contributions
            ],
            "total_weight_bps": (
                self.total_weight_bps
            ),
            "computed_at": (
                self.computed_at.isoformat()
            ),
            "schema_version": self.schema_version,
            "source_of_truth": (
                self.source_of_truth
            ),
            "trust_state": (
                self.trust_state.value
            ),
            "trust_version": self.trust_version,
            "trust_history": list(
                self.trust_history
            ),
            "provenance_references": list(
                self.provenance_references
            ),
            "confidence_metadata": dict(
                self.confidence_metadata
            ),
            "evidence_count": self.evidence_count,
        }


class TrustScoreEngine:
    """
    CORE-007 Trust Domain authority.

    Does not own:
    - fraud detection
    - risk rules
    - governance
    - authorization
    - approvals
    - events
    - Control Center state
    """

    MODEL_VERSION = TRUST_SCORE_MODEL_VERSION

    @classmethod
    def compute(
        cls,
        *,
        tenant_id: str,
        subject_id: str,
        signals: tuple[
            TrustSignal,
            ...
        ] | list[TrustSignal],
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

        normalized = tuple(signals)

        if not normalized:
            raise TrustScoreInsufficientEvidenceError(
                "Trust score requires at least one signal."
            )

        by_id: dict[str, TrustSignal] = {}

        for signal in normalized:
            if not isinstance(
                signal,
                TrustSignal,
            ):
                raise TrustScoreValidationError(
                    "signals must contain TrustSignal."
                )

            signal.assert_scope(
                tenant_id=tenant_id,
                subject_id=subject_id,
            )

            previous = by_id.get(
                signal.signal_id
            )

            if previous is not None:
                previous.assert_compatible(
                    signal
                )
                raise TrustScoreConflictError(
                    "Duplicate signal identity."
                )

            by_id[signal.signal_id] = signal

        ordered = tuple(
            by_id[key]
            for key in sorted(by_id)
        )

        contributions: list[
            TrustScoreContribution
        ] = []

        numerator = Decimal("0")
        total_weight = 0
        provenance: list[str] = []

        for signal in ordered:
            weight = model.weight_for(
                signal.category
            )

            contributions.append(
                TrustScoreContribution(
                    signal_id=signal.signal_id,
                    category=signal.category,
                    value=signal.value,
                    weight_bps=weight,
                )
            )

            numerator += (
                Decimal(signal.value)
                * Decimal(weight)
            )

            total_weight += weight
            provenance.append(
                signal.provenance_reference
            )

        if total_weight <= 0:
            raise TrustScoreInsufficientEvidenceError(
                "Total trust weight must be positive."
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

        normalized_time = _utc(
            computed_at,
            "computed_at",
        )

        history = tuple(
            sorted(
                {
                    signal.history_reference
                    for signal in ordered
                    if signal.history_reference
                }
            )
        )

        confidence_values = [
            signal.confidence_metadata
            for signal in ordered
            if signal.confidence_metadata
        ]

        return TrustScore(
            tenant_id=tenant_id,
            subject_id=subject_id,
            score=score,
            model_version=model.model_version,
            model_fingerprint=model.fingerprint,
            signal_ids=tuple(
                signal.signal_id
                for signal in ordered
            ),
            signal_fingerprints=tuple(
                signal.fingerprint
                for signal in ordered
            ),
            contributions=tuple(
                contributions
            ),
            total_weight_bps=total_weight,
            computed_at=normalized_time,
            trust_state=TrustState.ACTIVE,
            trust_version=max(
                signal.signal_version
                for signal in ordered
            ),
            trust_history=history,
            provenance_references=tuple(
                sorted(set(provenance))
            ),
            confidence_metadata={
                "signal_count": len(ordered),
                "signal_confidence_metadata": (
                    confidence_values
                ),
            },
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
    "TrustState",
    "TrustScoreDecisionBoundary",
    "TrustScoringModel",
    "TrustSignal",
    "TrustScoreContribution",
    "TrustScore",
    "TrustScoreEngine",
]
