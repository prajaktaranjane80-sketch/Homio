from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
import hashlib
import json

from ..lead_ownership.lead_fraud_handoff import (
    FraudHandoffPriority,
    FraudHandoffReason,
    LeadFraudHandoff,
)


FRAUD_DETECTION_SCHEMA_VERSION = 1
FRAUD_DETECTION_MODEL_VERSION = "1.0"


class FraudDetectionError(ValueError):
    """Base CORE-007 fraud detection error."""


class FraudDetectionValidationError(
    FraudDetectionError
):
    """Invalid fraud detection contract."""


class FraudDetectionScopeError(
    FraudDetectionError
):
    """Cross-tenant or subject violation."""


class FraudDetectionConflictError(
    FraudDetectionError
):
    """Conflicting immutable fraud identity."""


class FraudSeverity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudDetectionState(str, Enum):
    DETECTED = "DETECTED"
    REVIEW = "REVIEW"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CLOSED = "CLOSED"


class FraudFalsePositiveState(str, Enum):
    NOT_REVIEWED = "NOT_REVIEWED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CONFIRMED_FALSE_POSITIVE = (
        "CONFIRMED_FALSE_POSITIVE"
    )
    REJECTED = "REJECTED"


class FraudEscalationLevel(str, Enum):
    NONE = "NONE"
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudFindingCode(str, Enum):
    HANDOFF_DUPLICATE_LEAD = (
        "HANDOFF_DUPLICATE_LEAD"
    )
    HANDOFF_ATTRIBUTION_CONFLICT = (
        "HANDOFF_ATTRIBUTION_CONFLICT"
    )
    HANDOFF_OWNERSHIP_CONFLICT = (
        "HANDOFF_OWNERSHIP_CONFLICT"
    )
    HANDOFF_IDENTITY_REUSE = (
        "HANDOFF_IDENTITY_REUSE"
    )
    HANDOFF_EVIDENCE_CONFLICT = (
        "HANDOFF_EVIDENCE_CONFLICT"
    )
    HANDOFF_SUSPICIOUS_MUTATION = (
        "HANDOFF_SUSPICIOUS_MUTATION"
    )
    LEAD_SUBMISSION_VELOCITY = (
        "LEAD_SUBMISSION_VELOCITY"
    )
    GPS_MOCK_LOCATION = "GPS_MOCK_LOCATION"
    GPS_PROXY_DETECTED = "GPS_PROXY_DETECTED"
    GPS_IMPOSSIBLE_SPEED = "GPS_IMPOSSIBLE_SPEED"


_HANDOFF_CODE_BY_REASON = {
    FraudHandoffReason.DUPLICATE_LEAD: (
        FraudFindingCode.HANDOFF_DUPLICATE_LEAD
    ),
    FraudHandoffReason.ATTRIBUTION_CONFLICT: (
        FraudFindingCode.HANDOFF_ATTRIBUTION_CONFLICT
    ),
    FraudHandoffReason.OWNERSHIP_CONFLICT: (
        FraudFindingCode.HANDOFF_OWNERSHIP_CONFLICT
    ),
    FraudHandoffReason.IDENTITY_REUSE: (
        FraudFindingCode.HANDOFF_IDENTITY_REUSE
    ),
    FraudHandoffReason.EVIDENCE_CONFLICT: (
        FraudFindingCode.HANDOFF_EVIDENCE_CONFLICT
    ),
    FraudHandoffReason.SUSPICIOUS_MUTATION: (
        FraudFindingCode.HANDOFF_SUSPICIOUS_MUTATION
    ),
}


_HANDOFF_SEVERITY_BY_PRIORITY = {
    FraudHandoffPriority.LOW: FraudSeverity.REVIEW,
    FraudHandoffPriority.MEDIUM: FraudSeverity.HIGH,
    FraudHandoffPriority.HIGH: FraudSeverity.HIGH,
    FraudHandoffPriority.CRITICAL: (
        FraudSeverity.CRITICAL
    ),
}


def _uuid(value: Any, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise FraudDetectionValidationError(
            f"{field_name} must be UUID."
        )
    return value


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FraudDetectionValidationError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _time(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FraudDetectionValidationError(
            f"{field_name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise FraudDetectionValidationError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _refs(
    values: tuple[str, ...],
    field_name: str,
    *,
    required: bool = True,
) -> tuple[str, ...]:
    result = tuple(
        dict.fromkeys(
            _text(item, field_name)
            for item in values
        )
    )

    if required and not result:
        raise FraudDetectionValidationError(
            f"{field_name} must contain at least "
            "one reference."
        )

    return result


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
class FraudDetectionPolicy:
    """Versioned deterministic detection policy."""

    version: str = FRAUD_DETECTION_MODEL_VERSION
    velocity_window_seconds: int = 60
    max_submissions_in_window: int = 3
    max_plausible_speed_kmh: float = 180.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "version",
            _text(self.version, "version"),
        )

        for name in (
            "velocity_window_seconds",
            "max_submissions_in_window",
        ):
            value = getattr(self, name)

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):
                raise FraudDetectionValidationError(
                    f"{name} must be positive integer."
                )

        if (
            isinstance(
                self.max_plausible_speed_kmh,
                bool,
            )
            or not isinstance(
                self.max_plausible_speed_kmh,
                (int, float),
            )
            or self.max_plausible_speed_kmh <= 0
        ):
            raise FraudDetectionValidationError(
                "max_plausible_speed_kmh must be positive."
            )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "version": self.version,
                "velocity_window_seconds": (
                    self.velocity_window_seconds
                ),
                "max_submissions_in_window": (
                    self.max_submissions_in_window
                ),
                "max_plausible_speed_kmh": (
                    self.max_plausible_speed_kmh
                ),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "velocity_window_seconds": (
                self.velocity_window_seconds
            ),
            "max_submissions_in_window": (
                self.max_submissions_in_window
            ),
            "max_plausible_speed_kmh": (
                self.max_plausible_speed_kmh
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class LeadSubmissionObservation:
    submission_id: UUID
    tenant_id: UUID
    lead_id: UUID
    submitted_at: datetime
    evidence_reference: str
    source_reference: str

    def __post_init__(self) -> None:
        for name in (
            "submission_id",
            "tenant_id",
            "lead_id",
        ):
            _uuid(
                getattr(self, name),
                name,
            )

        object.__setattr__(
            self,
            "submitted_at",
            _time(
                self.submitted_at,
                "submitted_at",
            ),
        )

        object.__setattr__(
            self,
            "evidence_reference",
            _text(
                self.evidence_reference,
                "evidence_reference",
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

    @property
    def identity_key(
        self,
    ) -> tuple[UUID, UUID, UUID]:
        return (
            self.tenant_id,
            self.lead_id,
            self.submission_id,
        )

    def ensure_scope(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> None:
        if (
            self.tenant_id != tenant_id
            or self.lead_id != lead_id
        ):
            raise FraudDetectionScopeError(
                "Submission crosses tenant/subject scope."
            )


@dataclass(frozen=True, slots=True)
class VisitTelemetryObservation:
    observation_id: UUID
    tenant_id: UUID
    lead_id: UUID
    observed_at: datetime
    evidence_reference: str
    source_reference: str
    mock_location_provider: bool = False
    proxy_detected: bool = False
    speed_kmh: float | None = None

    def __post_init__(self) -> None:
        for name in (
            "observation_id",
            "tenant_id",
            "lead_id",
        ):
            _uuid(
                getattr(self, name),
                name,
            )

        object.__setattr__(
            self,
            "observed_at",
            _time(
                self.observed_at,
                "observed_at",
            ),
        )

        object.__setattr__(
            self,
            "evidence_reference",
            _text(
                self.evidence_reference,
                "evidence_reference",
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

        if self.speed_kmh is not None:
            if (
                isinstance(
                    self.speed_kmh,
                    bool,
                )
                or not isinstance(
                    self.speed_kmh,
                    (int, float),
                )
                or self.speed_kmh < 0
            ):
                raise FraudDetectionValidationError(
                    "speed_kmh must be >= 0."
                )

    def ensure_scope(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> None:
        if (
            self.tenant_id != tenant_id
            or self.lead_id != lead_id
        ):
            raise FraudDetectionScopeError(
                "Telemetry crosses tenant/subject scope."
            )


@dataclass(frozen=True, slots=True)
class FraudFinding:
    """Immutable evidence-linked fraud observation."""

    finding_id: UUID
    tenant_id: UUID
    subject_id: UUID
    code: FraudFindingCode
    severity: FraudSeverity
    message: str
    evidence_references: tuple[str, ...]
    source_references: tuple[str, ...]
    observed_at: datetime

    detection_rule_reference: str = (
        "CORE-007-FRAUD-DETECTION"
    )
    detection_input_provenance: tuple[str, ...] = ()
    anomaly_reference: str | None = None
    confidence: int = 100
    detection_state: FraudDetectionState = (
        FraudDetectionState.DETECTED
    )
    false_positive_state: FraudFalsePositiveState = (
        FraudFalsePositiveState.NOT_REVIEWED
    )
    escalation_level: FraudEscalationLevel = (
        FraudEscalationLevel.NONE
    )
    irreversible_action_protected: bool = True

    def __post_init__(self) -> None:
        for name in (
            "finding_id",
            "tenant_id",
            "subject_id",
        ):
            _uuid(
                getattr(self, name),
                name,
            )

        if not isinstance(
            self.code,
            FraudFindingCode,
        ):
            raise FraudDetectionValidationError(
                "code must be FraudFindingCode."
            )

        if not isinstance(
            self.severity,
            FraudSeverity,
        ):
            raise FraudDetectionValidationError(
                "severity must be FraudSeverity."
            )

        object.__setattr__(
            self,
            "message",
            _text(
                self.message,
                "message",
            ),
        )

        object.__setattr__(
            self,
            "evidence_references",
            _refs(
                self.evidence_references,
                "evidence_reference",
            ),
        )

        object.__setattr__(
            self,
            "source_references",
            _refs(
                self.source_references,
                "source_reference",
            ),
        )

        object.__setattr__(
            self,
            "detection_rule_reference",
            _text(
                self.detection_rule_reference,
                "detection_rule_reference",
            ),
        )

        object.__setattr__(
            self,
            "detection_input_provenance",
            _refs(
                self.detection_input_provenance,
                "detection_input_provenance",
                required=False,
            ),
        )

        if self.anomaly_reference is not None:
            object.__setattr__(
                self,
                "anomaly_reference",
                _text(
                    self.anomaly_reference,
                    "anomaly_reference",
                ),
            )

        if (
            isinstance(self.confidence, bool)
            or not isinstance(
                self.confidence,
                int,
            )
            or not 0 <= self.confidence <= 100
        ):
            raise FraudDetectionValidationError(
                "confidence must be 0..100."
            )

        if not isinstance(
            self.detection_state,
            FraudDetectionState,
        ):
            raise FraudDetectionValidationError(
                "Invalid detection_state."
            )

        if not isinstance(
            self.false_positive_state,
            FraudFalsePositiveState,
        ):
            raise FraudDetectionValidationError(
                "Invalid false_positive_state."
            )

        if not isinstance(
            self.escalation_level,
            FraudEscalationLevel,
        ):
            raise FraudDetectionValidationError(
                "Invalid escalation_level."
            )

        object.__setattr__(
            self,
            "observed_at",
            _time(
                self.observed_at,
                "observed_at",
            ),
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "finding_id": str(
                    self.finding_id
                ),
                "tenant_id": str(
                    self.tenant_id
                ),
                "subject_id": str(
                    self.subject_id
                ),
                "code": self.code.value,
                "severity": self.severity.value,
                "message": self.message,
                "evidence_references": (
                    self.evidence_references
                ),
                "source_references": (
                    self.source_references
                ),
                "observed_at": (
                    self.observed_at.isoformat()
                ),
                "detection_rule_reference": (
                    self.detection_rule_reference
                ),
                "detection_input_provenance": (
                    self.detection_input_provenance
                ),
                "anomaly_reference": (
                    self.anomaly_reference
                ),
                "confidence": self.confidence,
                "detection_state": (
                    self.detection_state.value
                ),
                "false_positive_state": (
                    self.false_positive_state.value
                ),
                "escalation_level": (
                    self.escalation_level.value
                ),
                "irreversible_action_protected": (
                    self.irreversible_action_protected
                ),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": str(
                self.finding_id
            ),
            "tenant_id": str(
                self.tenant_id
            ),
            "subject_id": str(
                self.subject_id
            ),
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "evidence_references": list(
                self.evidence_references
            ),
            "source_references": list(
                self.source_references
            ),
            "observed_at": (
                self.observed_at.isoformat()
            ),
            "detection_rule_reference": (
                self.detection_rule_reference
            ),
            "detection_input_provenance": list(
                self.detection_input_provenance
            ),
            "anomaly_reference": (
                self.anomaly_reference
            ),
            "confidence": self.confidence,
            "detection_state": (
                self.detection_state.value
            ),
            "false_positive_state": (
                self.false_positive_state.value
            ),
            "escalation_level": (
                self.escalation_level.value
            ),
            "irreversible_action_protected": (
                self.irreversible_action_protected
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class FraudAssessment:
    """Immutable fraud assessment and detection boundary."""

    assessment_id: UUID
    tenant_id: UUID
    subject_id: UUID
    correlation_id: str
    model_version: str
    policy_fingerprint: str
    findings: tuple[FraudFinding, ...]
    tripwire_raised: bool
    generated_at: datetime

    source_of_truth: str = "fraud_detection"

    detection_version: int = 1
    detection_input_provenance: tuple[str, ...] = ()
    false_positive_handling: str = (
        "HUMAN_REVIEW_BEFORE_IRREVERSIBLE_ACTION"
    )
    escalation_boundary: str = (
        "HIGH_OR_CRITICAL_REQUIRES_GOVERNANCE_REVIEW"
    )
    irreversible_action_protected: bool = True

    def __post_init__(self) -> None:
        for name in (
            "assessment_id",
            "tenant_id",
            "subject_id",
        ):
            _uuid(
                getattr(self, name),
                name,
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
            "model_version",
            _text(
                self.model_version,
                "model_version",
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
            self.findings,
            tuple,
        ):
            raise FraudDetectionValidationError(
                "findings must be tuple."
            )

        for finding in self.findings:
            if not isinstance(
                finding,
                FraudFinding,
            ):
                raise FraudDetectionValidationError(
                    "findings must contain FraudFinding."
                )

            if (
                finding.tenant_id
                != self.tenant_id
                or finding.subject_id
                != self.subject_id
            ):
                raise FraudDetectionScopeError(
                    "Finding crosses assessment scope."
                )

        object.__setattr__(
            self,
            "generated_at",
            _time(
                self.generated_at,
                "generated_at",
            ),
        )

        if (
            isinstance(
                self.detection_version,
                bool,
            )
            or not isinstance(
                self.detection_version,
                int,
            )
            or self.detection_version < 1
        ):
            raise FraudDetectionValidationError(
                "detection_version must be >= 1."
            )

        object.__setattr__(
            self,
            "detection_input_provenance",
            _refs(
                self.detection_input_provenance,
                "detection_input_provenance",
                required=False,
            ),
        )

        object.__setattr__(
            self,
            "false_positive_handling",
            _text(
                self.false_positive_handling,
                "false_positive_handling",
            ),
        )

        object.__setattr__(
            self,
            "escalation_boundary",
            _text(
                self.escalation_boundary,
                "escalation_boundary",
            ),
        )

    @property
    def identity_key(
        self,
    ) -> tuple[UUID, UUID, str]:
        return (
            self.tenant_id,
            self.subject_id,
            self.correlation_id,
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "assessment_id": str(
                    self.assessment_id
                ),
                "tenant_id": str(
                    self.tenant_id
                ),
                "subject_id": str(
                    self.subject_id
                ),
                "correlation_id": (
                    self.correlation_id
                ),
                "model_version": (
                    self.model_version
                ),
                "policy_fingerprint": (
                    self.policy_fingerprint
                ),
                "findings": tuple(
                    item.fingerprint
                    for item in self.findings
                ),
                "tripwire_raised": (
                    self.tripwire_raised
                ),
                "generated_at": (
                    self.generated_at.isoformat()
                ),
                "detection_version": (
                    self.detection_version
                ),
                "detection_input_provenance": (
                    self.detection_input_provenance
                ),
                "false_positive_handling": (
                    self.false_positive_handling
                ),
                "escalation_boundary": (
                    self.escalation_boundary
                ),
                "irreversible_action_protected": (
                    self.irreversible_action_protected
                ),
            }
        )

    def assert_compatible(
        self,
        other: "FraudAssessment",
    ) -> None:
        if not isinstance(
            other,
            FraudAssessment,
        ):
            raise FraudDetectionValidationError(
                "other must be FraudAssessment."
            )

        if (
            self.identity_key
            != other.identity_key
        ):
            raise FraudDetectionConflictError(
                "Assessment identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise FraudDetectionConflictError(
                "Same assessment identity has "
                "conflicting fraud result."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": str(
                self.assessment_id
            ),
            "tenant_id": str(
                self.tenant_id
            ),
            "subject_id": str(
                self.subject_id
            ),
            "correlation_id": (
                self.correlation_id
            ),
            "model_version": (
                self.model_version
            ),
            "policy_fingerprint": (
                self.policy_fingerprint
            ),
            "findings": [
                item.to_dict()
                for item in self.findings
            ],
            "tripwire_raised": (
                self.tripwire_raised
            ),
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "source_of_truth": (
                self.source_of_truth
            ),
            "detection_version": (
                self.detection_version
            ),
            "detection_input_provenance": list(
                self.detection_input_provenance
            ),
            "false_positive_handling": (
                self.false_positive_handling
            ),
            "escalation_boundary": (
                self.escalation_boundary
            ),
            "irreversible_action_protected": (
                self.irreversible_action_protected
            ),
            "fingerprint": self.fingerprint,
        }


def _severity_confidence(
    severity: FraudSeverity,
) -> int:
    return {
        FraudSeverity.INFORMATIONAL: 50,
        FraudSeverity.REVIEW: 70,
        FraudSeverity.HIGH: 90,
        FraudSeverity.CRITICAL: 100,
    }[severity]


def _escalation_for(
    severity: FraudSeverity,
) -> FraudEscalationLevel:
    return {
        FraudSeverity.INFORMATIONAL: (
            FraudEscalationLevel.NONE
        ),
        FraudSeverity.REVIEW: (
            FraudEscalationLevel.REVIEW
        ),
        FraudSeverity.HIGH: (
            FraudEscalationLevel.HIGH
        ),
        FraudSeverity.CRITICAL: (
            FraudEscalationLevel.CRITICAL
        ),
    }[severity]


class FraudDetectionEngine:
    """
    CORE-007 fraud detection authority.

    Produces observations only.

    It does not:
    - authorize actions,
    - execute punishment,
    - approve transactions,
    - publish events,
    - own governance,
    - own Control Center state.
    """

    def detect(
        self,
        *,
        tenant_id: UUID,
        subject_id: UUID,
        correlation_id: str,
        handoffs: tuple[
            LeadFraudHandoff,
            ...
        ] = (),
        submissions: tuple[
            LeadSubmissionObservation,
            ...
        ] = (),
        visit_observations: tuple[
            VisitTelemetryObservation,
            ...
        ] = (),
        policy: FraudDetectionPolicy | None = None,
        assessment_id: UUID | None = None,
        generated_at: datetime | None = None,
    ) -> FraudAssessment:
        _uuid(
            tenant_id,
            "tenant_id",
        )
        _uuid(
            subject_id,
            "subject_id",
        )

        correlation_id = _text(
            correlation_id,
            "correlation_id",
        )

        policy = (
            policy
            or FraudDetectionPolicy()
        )

        for handoff in handoffs:
            if not isinstance(
                handoff,
                LeadFraudHandoff,
            ):
                raise FraudDetectionValidationError(
                    "handoffs must contain LeadFraudHandoff."
                )

            handoff.ensure_tenant(
                tenant_id
            )

            if handoff.lead_id != subject_id:
                raise FraudDetectionScopeError(
                    "Fraud handoff does not "
                    "match assessment subject."
                )

        for observation in submissions:
            if not isinstance(
                observation,
                LeadSubmissionObservation,
            ):
                raise FraudDetectionValidationError(
                    "submissions must contain "
                    "LeadSubmissionObservation."
                )

            observation.ensure_scope(
                tenant_id=tenant_id,
                lead_id=subject_id,
            )

        for observation in visit_observations:
            if not isinstance(
                observation,
                VisitTelemetryObservation,
            ):
                raise FraudDetectionValidationError(
                    "visit_observations must contain "
                    "VisitTelemetryObservation."
                )

            observation.ensure_scope(
                tenant_id=tenant_id,
                lead_id=subject_id,
            )

        findings: list[FraudFinding] = []

        findings.extend(
            self._handoff_findings(
                handoffs=tuple(handoffs),
                tenant_id=tenant_id,
                subject_id=subject_id,
            )
        )

        velocity = self._velocity_finding(
            submissions=tuple(submissions),
            tenant_id=tenant_id,
            subject_id=subject_id,
            policy=policy,
        )

        if velocity is not None:
            findings.append(velocity)

        findings.extend(
            self._telemetry_findings(
                visit_observations=tuple(
                    visit_observations
                ),
                tenant_id=tenant_id,
                subject_id=subject_id,
                policy=policy,
            )
        )

        findings.sort(
            key=lambda item: (
                item.severity.value,
                item.code.value,
                str(item.finding_id),
            )
        )

        findings = list(
            {
                item.fingerprint: item
                for item in findings
            }.values()
        )

        findings.sort(
            key=lambda item: item.fingerprint
        )

        tripwire = any(
            item.severity
            in {
                FraudSeverity.HIGH,
                FraudSeverity.CRITICAL,
            }
            for item in findings
        )

        provenance = tuple(
            sorted(
                {
                    ref
                    for finding in findings
                    for ref in (
                        finding.detection_input_provenance
                    )
                }
            )
        )

        return FraudAssessment(
            assessment_id=(
                assessment_id
                or uuid4()
            ),
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            model_version=(
                FRAUD_DETECTION_MODEL_VERSION
            ),
            policy_fingerprint=(
                policy.fingerprint
            ),
            findings=tuple(findings),
            tripwire_raised=tripwire,
            generated_at=_time(
                generated_at
                or datetime.now(timezone.utc),
                "generated_at",
            ),
            detection_version=1,
            detection_input_provenance=provenance,
        )

    def _handoff_findings(
        self,
        *,
        handoffs: tuple[
            LeadFraudHandoff,
            ...
        ],
        tenant_id: UUID,
        subject_id: UUID,
    ) -> list[FraudFinding]:
        results: list[FraudFinding] = []

        seen: dict[
            tuple[Any, ...],
            LeadFraudHandoff,
        ] = {}

        for handoff in sorted(
            handoffs,
            key=lambda item: (
                item.handoff_key,
                str(item.created_at),
            ),
        ):
            existing = seen.get(
                handoff.handoff_key
            )

            if existing is not None:
                existing.assert_compatible(
                    handoff
                )
                continue

            seen[
                handoff.handoff_key
            ] = handoff

            severity = (
                _HANDOFF_SEVERITY_BY_PRIORITY[
                    handoff.priority
                ]
            )

            results.append(
                FraudFinding(
                    finding_id=uuid4(),
                    tenant_id=tenant_id,
                    subject_id=subject_id,
                    code=(
                        _HANDOFF_CODE_BY_REASON[
                            handoff.reason
                        ]
                    ),
                    severity=severity,
                    message=(
                        "CORE-003 fraud handoff received: "
                        f"{handoff.reason.value}"
                    ),
                    evidence_references=(
                        tuple(
                            handoff.evidence_references
                        )
                    ),
                    source_references=(
                        (
                            handoff.source_reference,
                        )
                    ),
                    observed_at=(
                        handoff.created_at
                    ),
                    detection_rule_reference=(
                        "CORE-003-FRAUD-HANDOFF"
                    ),
                    detection_input_provenance=(
                        (
                            handoff.source_reference,
                        )
                    ),
                    anomaly_reference=(
                        str(
                            handoff.handoff_key
                        )
                    ),
                    confidence=_severity_confidence(
                        severity
                    ),
                    detection_state=(
                        FraudDetectionState.DETECTED
                    ),
                    false_positive_state=(
                        FraudFalsePositiveState.REVIEW_REQUIRED
                    ),
                    escalation_level=_escalation_for(
                        severity
                    ),
                    irreversible_action_protected=True,
                )
            )

        return results

    def _velocity_finding(
        self,
        *,
        submissions: tuple[
            LeadSubmissionObservation,
            ...
        ],
        tenant_id: UUID,
        subject_id: UUID,
        policy: FraudDetectionPolicy,
    ) -> FraudFinding | None:
        if not submissions:
            return None

        ordered = sorted(
            submissions,
            key=lambda item: (
                item.submitted_at,
                str(item.submission_id),
            ),
        )

        latest = ordered[-1]

        window_start = (
            latest.submitted_at
            - timedelta(
                seconds=policy.velocity_window_seconds
            )
        )

        windowed = tuple(
            item
            for item in ordered
            if (
                window_start
                <= item.submitted_at
                <= latest.submitted_at
            )
        )

        if (
            len(windowed)
            <= policy.max_submissions_in_window
        ):
            return None

        return FraudFinding(
            finding_id=uuid4(),
            tenant_id=tenant_id,
            subject_id=subject_id,
            code=(
                FraudFindingCode
                .LEAD_SUBMISSION_VELOCITY
            ),
            severity=FraudSeverity.HIGH,
            message=(
                "Lead submission velocity exceeds "
                "configured fraud threshold."
            ),
            evidence_references=tuple(
                item.evidence_reference
                for item in windowed
            ),
            source_references=tuple(
                sorted(
                    {
                        item.source_reference
                        for item in windowed
                    }
                )
            ),
            observed_at=latest.submitted_at,
            detection_rule_reference=(
                "CORE-007-T02.VELOCITY"
            ),
            detection_input_provenance=tuple(
                sorted(
                    {
                        item.source_reference
                        for item in windowed
                    }
                )
            ),
            anomaly_reference=(
                f"velocity:{subject_id}:"
                f"{latest.submitted_at.isoformat()}"
            ),
            confidence=90,
            detection_state=(
                FraudDetectionState.DETECTED
            ),
            false_positive_state=(
                FraudFalsePositiveState.REVIEW_REQUIRED
            ),
            escalation_level=(
                FraudEscalationLevel.HIGH
            ),
            irreversible_action_protected=True,
        )

    def _telemetry_findings(
        self,
        *,
        visit_observations: tuple[
            VisitTelemetryObservation,
            ...
        ],
        tenant_id: UUID,
        subject_id: UUID,
        policy: FraudDetectionPolicy,
    ) -> list[FraudFinding]:
        results: list[FraudFinding] = []

        for observation in sorted(
            visit_observations,
            key=lambda item: str(
                item.observation_id
            ),
        ):
            if observation.mock_location_provider:
                results.append(
                    FraudFinding(
                        finding_id=uuid4(),
                        tenant_id=tenant_id,
                        subject_id=subject_id,
                        code=(
                            FraudFindingCode
                            .GPS_MOCK_LOCATION
                        ),
                        severity=(
                            FraudSeverity.CRITICAL
                        ),
                        message=(
                            "Telemetry reports a "
                            "mock-location provider."
                        ),
                        evidence_references=(
                            observation.evidence_reference,
                        ),
                        source_references=(
                            observation.source_reference,
                        ),
                        observed_at=(
                            observation.observed_at
                        ),
                        detection_rule_reference=(
                            "CORE-007-T02.GPS_MOCK"
                        ),
                        detection_input_provenance=(
                            observation.source_reference,
                        ),
                        anomaly_reference=(
                            str(
                                observation.observation_id
                            )
                        ),
                        confidence=100,
                        detection_state=(
                            FraudDetectionState.DETECTED
                        ),
                        false_positive_state=(
                            FraudFalsePositiveState
                            .REVIEW_REQUIRED
                        ),
                        escalation_level=(
                            FraudEscalationLevel.CRITICAL
                        ),
                        irreversible_action_protected=True,
                    )
                )

            if observation.proxy_detected:
                results.append(
                    FraudFinding(
                        finding_id=uuid4(),
                        tenant_id=tenant_id,
                        subject_id=subject_id,
                        code=(
                            FraudFindingCode
                            .GPS_PROXY_DETECTED
                        ),
                        severity=FraudSeverity.HIGH,
                        message=(
                            "Telemetry reports a "
                            "proxy signal."
                        ),
                        evidence_references=(
                            observation.evidence_reference,
                        ),
                        source_references=(
                            observation.source_reference,
                        ),
                        observed_at=(
                            observation.observed_at
                        ),
                        detection_rule_reference=(
                            "CORE-007-T02.GPS_PROXY"
                        ),
                        detection_input_provenance=(
                            observation.source_reference,
                        ),
                        anomaly_reference=(
                            str(
                                observation.observation_id
                            )
                        ),
                        confidence=90,
                        detection_state=(
                            FraudDetectionState.DETECTED
                        ),
                        false_positive_state=(
                            FraudFalsePositiveState
                            .REVIEW_REQUIRED
                        ),
                        escalation_level=(
                            FraudEscalationLevel.HIGH
                        ),
                        irreversible_action_protected=True,
                    )
                )

            if (
                observation.speed_kmh is not None
                and (
                    observation.speed_kmh
                    > policy.max_plausible_speed_kmh
                )
            ):
                results.append(
                    FraudFinding(
                        finding_id=uuid4(),
                        tenant_id=tenant_id,
                        subject_id=subject_id,
                        code=(
                            FraudFindingCode
                            .GPS_IMPOSSIBLE_SPEED
                        ),
                        severity=FraudSeverity.HIGH,
                        message=(
                            "Telemetry speed exceeds "
                            "configured plausibility threshold."
                        ),
                        evidence_references=(
                            observation.evidence_reference,
                        ),
                        source_references=(
                            observation.source_reference,
                        ),
                        observed_at=(
                            observation.observed_at
                        ),
                        detection_rule_reference=(
                            "CORE-007-T02.GPS_SPEED"
                        ),
                        detection_input_provenance=(
                            observation.source_reference,
                        ),
                        anomaly_reference=(
                            str(
                                observation.observation_id
                            )
                        ),
                        confidence=90,
                        detection_state=(
                            FraudDetectionState.DETECTED
                        ),
                        false_positive_state=(
                            FraudFalsePositiveState
                            .REVIEW_REQUIRED
                        ),
                        escalation_level=(
                            FraudEscalationLevel.HIGH
                        ),
                        irreversible_action_protected=True,
                    )
                )

        return results


__all__ = [
    "FRAUD_DETECTION_SCHEMA_VERSION",
    "FRAUD_DETECTION_MODEL_VERSION",
    "FraudDetectionError",
    "FraudDetectionValidationError",
    "FraudDetectionScopeError",
    "FraudDetectionConflictError",
    "FraudSeverity",
    "FraudDetectionState",
    "FraudFalsePositiveState",
    "FraudEscalationLevel",
    "FraudFindingCode",
    "FraudDetectionPolicy",
    "LeadSubmissionObservation",
    "VisitTelemetryObservation",
    "FraudFinding",
    "FraudAssessment",
    "FraudDetectionEngine",
]
