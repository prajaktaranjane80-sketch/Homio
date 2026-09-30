"""CORE-007 T03 - Risk Assessment Evaluation Policy.

This is an evaluation policy, not a governance policy.

Governance policy ownership remains reserved for CORE-007 T04.
This module only defines deterministic inputs-to-risk-classification
mapping for the T03 assessment boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from .fraud_detection import FraudSeverity
from .risk_assessment import (
    RiskAssessmentValidationError,
    RiskLevel,
)


RISK_ASSESSMENT_POLICY_SCHEMA_VERSION = 1
RISK_ASSESSMENT_POLICY_VERSION = "1.0"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RiskAssessmentValidationError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _non_negative_int(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise RiskAssessmentValidationError(
            f"{field_name} must be an integer >= 0."
        )
    return value


def _bounded_int(
    value: Any,
    field_name: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
        or value > maximum
    ):
        raise RiskAssessmentValidationError(
            f"{field_name} must be an integer between "
            f"{minimum} and {maximum}."
        )
    return value


def _canonicalize(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }

    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]

    if (
        isinstance(value, (str, int, float, bool))
        or value is None
    ):
        return value

    raise RiskAssessmentValidationError(
        "Unsupported policy value type."
    )


def _fingerprint(value: Any) -> str:
    canonical = json.dumps(
        _canonicalize(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class TrustRiskBand:
    """Maps a trust-score interval to deterministic risk contribution."""

    minimum_score: int
    maximum_score: int
    risk_level: RiskLevel
    contribution_points: int
    rule_code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "minimum_score",
            _bounded_int(
                self.minimum_score,
                "minimum_score",
                minimum=0,
                maximum=100,
            ),
        )

        object.__setattr__(
            self,
            "maximum_score",
            _bounded_int(
                self.maximum_score,
                "maximum_score",
                minimum=0,
                maximum=100,
            ),
        )

        if self.minimum_score > self.maximum_score:
            raise RiskAssessmentValidationError(
                "minimum_score cannot exceed maximum_score."
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
            "contribution_points",
            _non_negative_int(
                self.contribution_points,
                "contribution_points",
            ),
        )

        object.__setattr__(
            self,
            "rule_code",
            _text(self.rule_code, "rule_code"),
        )


@dataclass(frozen=True, slots=True)
class RiskScoreLevelBand:
    """Maps final capped risk score to risk classification."""

    minimum_score: int
    maximum_score: int
    risk_level: RiskLevel

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "minimum_score",
            _bounded_int(
                self.minimum_score,
                "minimum_score",
                minimum=0,
                maximum=100,
            ),
        )

        object.__setattr__(
            self,
            "maximum_score",
            _bounded_int(
                self.maximum_score,
                "maximum_score",
                minimum=0,
                maximum=100,
            ),
        )

        if self.minimum_score > self.maximum_score:
            raise RiskAssessmentValidationError(
                "minimum_score cannot exceed maximum_score."
            )

        if not isinstance(
            self.risk_level,
            RiskLevel,
        ):
            raise RiskAssessmentValidationError(
                "risk_level must be RiskLevel."
            )


@dataclass(frozen=True, slots=True)
class RiskAssessmentPolicy:
    """Versioned deterministic T03 evaluation policy."""

    policy_id: str
    policy_version: str
    trust_score_bands: tuple[TrustRiskBand, ...]
    fraud_severity_points: Mapping[
        FraudSeverity,
        int,
    ]
    fraud_severity_levels: Mapping[
        FraudSeverity,
        RiskLevel,
    ]
    final_score_bands: tuple[RiskScoreLevelBand, ...]
    schema_version: int = (
        RISK_ASSESSMENT_POLICY_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _text(self.policy_id, "policy_id"),
        )

        object.__setattr__(
            self,
            "policy_version",
            _text(
                self.policy_version,
                "policy_version",
            ),
        )

        if not isinstance(
            self.trust_score_bands,
            tuple,
        ) or not self.trust_score_bands:
            raise RiskAssessmentValidationError(
                "trust_score_bands must be a non-empty tuple."
            )

        for band in self.trust_score_bands:
            if not isinstance(
                band,
                TrustRiskBand,
            ):
                raise RiskAssessmentValidationError(
                    "trust_score_bands must contain TrustRiskBand."
                )

        ordered_trust = tuple(
            sorted(
                self.trust_score_bands,
                key=lambda item: (
                    item.minimum_score,
                    item.maximum_score,
                ),
            )
        )

        if (
            ordered_trust[0].minimum_score != 0
            or ordered_trust[-1].maximum_score != 100
        ):
            raise RiskAssessmentValidationError(
                "Trust score bands must cover 0..100."
            )

        previous_max = -1

        for band in ordered_trust:
            if band.minimum_score != previous_max + 1:
                raise RiskAssessmentValidationError(
                    "Trust score bands must be contiguous "
                    "and non-overlapping."
                )
            previous_max = band.maximum_score

        object.__setattr__(
            self,
            "trust_score_bands",
            ordered_trust,
        )

        normalized_points = dict(
            self.fraud_severity_points
        )

        if set(normalized_points) != set(FraudSeverity):
            raise RiskAssessmentValidationError(
                "fraud_severity_points must define every FraudSeverity."
            )

        for severity, points in normalized_points.items():
            if not isinstance(
                severity,
                FraudSeverity,
            ):
                raise RiskAssessmentValidationError(
                    "Invalid fraud severity key."
                )

            normalized_points[severity] = (
                _non_negative_int(
                    points,
                    f"fraud_severity_points[{severity.value}]",
                )
            )

        object.__setattr__(
            self,
            "fraud_severity_points",
            MappingProxyType(normalized_points),
        )

        normalized_levels = dict(
            self.fraud_severity_levels
        )

        if set(normalized_levels) != set(FraudSeverity):
            raise RiskAssessmentValidationError(
                "fraud_severity_levels must define every FraudSeverity."
            )

        for severity, level in normalized_levels.items():
            if not isinstance(
                severity,
                FraudSeverity,
            ):
                raise RiskAssessmentValidationError(
                    "Invalid fraud severity key."
                )

            if not isinstance(
                level,
                RiskLevel,
            ):
                raise RiskAssessmentValidationError(
                    "Fraud severity mapping must contain RiskLevel."
                )

        object.__setattr__(
            self,
            "fraud_severity_levels",
            MappingProxyType(normalized_levels),
        )

        if not isinstance(
            self.final_score_bands,
            tuple,
        ) or not self.final_score_bands:
            raise RiskAssessmentValidationError(
                "final_score_bands must be a non-empty tuple."
            )

        for band in self.final_score_bands:
            if not isinstance(
                band,
                RiskScoreLevelBand,
            ):
                raise RiskAssessmentValidationError(
                    "final_score_bands must contain "
                    "RiskScoreLevelBand."
                )

        ordered_final = tuple(
            sorted(
                self.final_score_bands,
                key=lambda item: (
                    item.minimum_score,
                    item.maximum_score,
                ),
            )
        )

        if (
            ordered_final[0].minimum_score != 0
            or ordered_final[-1].maximum_score != 100
        ):
            raise RiskAssessmentValidationError(
                "Final risk-score bands must cover 0..100."
            )

        previous_max = -1

        for band in ordered_final:
            if band.minimum_score != previous_max + 1:
                raise RiskAssessmentValidationError(
                    "Final risk-score bands must be contiguous "
                    "and non-overlapping."
                )
            previous_max = band.maximum_score

        object.__setattr__(
            self,
            "final_score_bands",
            ordered_final,
        )

        if self.schema_version != (
            RISK_ASSESSMENT_POLICY_SCHEMA_VERSION
        ):
            raise RiskAssessmentValidationError(
                "Unsupported risk-assessment policy schema version."
            )

    @classmethod
    def baseline(cls) -> "RiskAssessmentPolicy":
        """Return the versioned CORE-007 T03 baseline policy."""

        return cls(
            policy_id="CORE-007-T03-RISK-BASELINE",
            policy_version=RISK_ASSESSMENT_POLICY_VERSION,
            trust_score_bands=(
                TrustRiskBand(
                    minimum_score=0,
                    maximum_score=19,
                    risk_level=RiskLevel.CRITICAL,
                    contribution_points=100,
                    rule_code="TRUST_0_19",
                ),
                TrustRiskBand(
                    minimum_score=20,
                    maximum_score=39,
                    risk_level=RiskLevel.HIGH,
                    contribution_points=70,
                    rule_code="TRUST_20_39",
                ),
                TrustRiskBand(
                    minimum_score=40,
                    maximum_score=59,
                    risk_level=RiskLevel.MEDIUM,
                    contribution_points=45,
                    rule_code="TRUST_40_59",
                ),
                TrustRiskBand(
                    minimum_score=60,
                    maximum_score=79,
                    risk_level=RiskLevel.LOW,
                    contribution_points=20,
                    rule_code="TRUST_60_79",
                ),
                TrustRiskBand(
                    minimum_score=80,
                    maximum_score=100,
                    risk_level=RiskLevel.INFORMATIONAL,
                    contribution_points=0,
                    rule_code="TRUST_80_100",
                ),
            ),
            fraud_severity_points={
                FraudSeverity.INFORMATIONAL: 0,
                FraudSeverity.REVIEW: 30,
                FraudSeverity.HIGH: 70,
                FraudSeverity.CRITICAL: 100,
            },
            fraud_severity_levels={
                FraudSeverity.INFORMATIONAL:
                    RiskLevel.INFORMATIONAL,
                FraudSeverity.REVIEW:
                    RiskLevel.MEDIUM,
                FraudSeverity.HIGH:
                    RiskLevel.HIGH,
                FraudSeverity.CRITICAL:
                    RiskLevel.CRITICAL,
            },
            final_score_bands=(
                RiskScoreLevelBand(
                    minimum_score=0,
                    maximum_score=24,
                    risk_level=RiskLevel.INFORMATIONAL,
                ),
                RiskScoreLevelBand(
                    minimum_score=25,
                    maximum_score=49,
                    risk_level=RiskLevel.LOW,
                ),
                RiskScoreLevelBand(
                    minimum_score=50,
                    maximum_score=74,
                    risk_level=RiskLevel.MEDIUM,
                ),
                RiskScoreLevelBand(
                    minimum_score=75,
                    maximum_score=99,
                    risk_level=RiskLevel.HIGH,
                ),
                RiskScoreLevelBand(
                    minimum_score=100,
                    maximum_score=100,
                    risk_level=RiskLevel.CRITICAL,
                ),
            ),
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "policy_id": self.policy_id,
                "policy_version": self.policy_version,
                "trust_score_bands": [
                    {
                        "minimum_score": band.minimum_score,
                        "maximum_score": band.maximum_score,
                        "risk_level": band.risk_level,
                        "contribution_points": (
                            band.contribution_points
                        ),
                        "rule_code": band.rule_code,
                    }
                    for band in self.trust_score_bands
                ],
                "fraud_severity_points": (
                    self.fraud_severity_points
                ),
                "fraud_severity_levels": (
                    self.fraud_severity_levels
                ),
                "final_score_bands": [
                    {
                        "minimum_score": band.minimum_score,
                        "maximum_score": band.maximum_score,
                        "risk_level": band.risk_level,
                    }
                    for band in self.final_score_bands
                ],
                "schema_version": self.schema_version,
            }
        )

    def trust_score_rule(
        self,
        score: int,
    ) -> TrustRiskBand:
        score = _bounded_int(
            score,
            "score",
            minimum=0,
            maximum=100,
        )

        for band in self.trust_score_bands:
            if (
                band.minimum_score
                <= score
                <= band.maximum_score
            ):
                return band

        raise RiskAssessmentValidationError(
            "No trust-score rule matched supplied score."
        )

    def fraud_points(
        self,
        severity: FraudSeverity,
    ) -> int:
        if not isinstance(
            severity,
            FraudSeverity,
        ):
            raise RiskAssessmentValidationError(
                "severity must be FraudSeverity."
            )

        return self.fraud_severity_points[severity]

    def fraud_level(
        self,
        severity: FraudSeverity,
    ) -> RiskLevel:
        if not isinstance(
            severity,
            FraudSeverity,
        ):
            raise RiskAssessmentValidationError(
                "severity must be FraudSeverity."
            )

        return self.fraud_severity_levels[severity]

    def final_level(
        self,
        risk_score: int,
    ) -> RiskLevel:
        risk_score = _bounded_int(
            risk_score,
            "risk_score",
            minimum=0,
            maximum=100,
        )

        for band in self.final_score_bands:
            if (
                band.minimum_score
                <= risk_score
                <= band.maximum_score
            ):
                return band.risk_level

        raise RiskAssessmentValidationError(
            "No final risk-score rule matched supplied score."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "trust_score_bands": [
                {
                    "minimum_score": band.minimum_score,
                    "maximum_score": band.maximum_score,
                    "risk_level": band.risk_level.value,
                    "contribution_points": (
                        band.contribution_points
                    ),
                    "rule_code": band.rule_code,
                }
                for band in self.trust_score_bands
            ],
            "fraud_severity_points": {
                key.value: value
                for key, value in self.fraud_severity_points.items()
            },
            "fraud_severity_levels": {
                key.value: value.value
                for key, value in self.fraud_severity_levels.items()
            },
            "final_score_bands": [
                {
                    "minimum_score": band.minimum_score,
                    "maximum_score": band.maximum_score,
                    "risk_level": band.risk_level.value,
                }
                for band in self.final_score_bands
            ],
            "schema_version": self.schema_version,
            "fingerprint": self.fingerprint,
        }
