"""CORE-007 T02 â€” Fraud Detection Integration.

ARCH-016 bounded fraud-detection authority.

This module:
- consumes fraud handoffs from CORE-003,
- evaluates concrete fraud observations,
- produces immutable evidence-linked findings,
- raises a fraud tripwire when HIGH/CRITICAL evidence is present.

This module does NOT:
- own lead lifecycle,
- own lead ownership,
- calculate trust scores,
- evaluate governance policy,
- authorize/deny business actions,
- require approval,
- publish events,
- own Control Center state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID, uuid4

from ..lead_ownership.lead_fraud_handoff import (
    FraudHandoffPriority,
    FraudHandoffReason,
    LeadFraudHandoff,
)


FRAUD_DETECTION_SCHEMA_VERSION = 1
FRAUD_DETECTION_MODEL_VERSION = "1.0"


class FraudDetectionError(Exception):
    """Base CORE-007 fraud detection error."""


class FraudDetectionValidationError(FraudDetectionError):
    """Invalid fraud detection data."""


class FraudDetectionScopeError(FraudDetectionError):
    """Cross-tenant or subject-scope violation."""


class FraudDetectionConflictError(FraudDetectionError):
    """Conflicting assessment identity."""


class FraudSeverity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudFindingCode(str, Enum):
    HANDOFF_DUPLICATE_LEAD = "HANDOFF_DUPLICATE_LEAD"
    HANDOFF_ATTRIBUTION_CONFLICT = "HANDOFF_ATTRIBUTION_CONFLICT"
    HANDOFF_OWNERSHIP_CONFLICT = "HANDOFF_OWNERSHIP_CONFLICT"
    HANDOFF_IDENTITY_REUSE = "HANDOFF_IDENTITY_REUSE"
    HANDOFF_EVIDENCE_CONFLICT = "HANDOFF_EVIDENCE_CONFLICT"
    HANDOFF_SUSPICIOUS_MUTATION = "HANDOFF_SUSPICIOUS_MUTATION"
    LEAD_SUBMISSION_VELOCITY = "LEAD_SUBMISSION_VELOCITY"
    GPS_MOCK_LOCATION = "GPS_MOCK_LOCATION"
    GPS_PROXY_DETECTED = "GPS_PROXY_DETECTED"
    GPS_IMPOSSIBLE_SPEED = "GPS_IMPOSSIBLE_SPEED"


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise FraudDetectionValidationError(
            f"{field_name} must be UUID"
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FraudDetectionValidationError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FraudDetectionValidationError(
            f"{field_name} must be datetime"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise FraudDetectionValidationError(
            f"{field_name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _references(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    if not values:
        raise FraudDetectionValidationError(
            f"{field_name} must contain at least one reference"
        )

    normalized = tuple(
        dict.fromkeys(
            _text(value, field_name)
            for value in values
        )
    )

    if not normalized:
        raise FraudDetectionValidationError(
            f"{field_name} must contain at least one reference"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class FraudDetectionPolicy:
    """Versioned deterministic fraud-detection parameters."""

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

        if (
            not isinstance(self.velocity_window_seconds, int)
            or isinstance(self.velocity_window_seconds, bool)
            or self.velocity_window_seconds <= 0
        ):
            raise FraudDetectionValidationError(
                "velocity_window_seconds must be positive integer"
            )

        if (
            not isinstance(self.max_submissions_in_window, int)
            or isinstance(self.max_submissions_in_window, bool)
            or self.max_submissions_in_window <= 0
        ):
            raise FraudDetectionValidationError(
                "max_submissions_in_window must be positive integer"
            )

        if (
            not isinstance(self.max_plausible_speed_kmh, (int, float))
            or isinstance(self.max_plausible_speed_kmh, bool)
            or self.max_plausible_speed_kmh <= 0
        ):
            raise FraudDetectionValidationError(
                "max_plausible_speed_kmh must be positive number"
            )

    @property
    def fingerprint(self) -> str:
        payload = {
            "version": self.version,
            "velocity_window_seconds": self.velocity_window_seconds,
            "max_submissions_in_window": (
                self.max_submissions_in_window
            ),
            "max_plausible_speed_kmh": (
                self.max_plausible_speed_kmh
            ),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
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
    """Evidence-backed lead submission observation."""

    submission_id: UUID
    tenant_id: UUID
    lead_id: UUID
    submitted_at: datetime
    evidence_reference: str
    source_reference: str

    def __post_init__(self) -> None:
        _uuid(self.submission_id, "submission_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.lead_id, "lead_id")
        object.__setattr__(
            self,
            "submitted_at",
            _time(self.submitted_at, "submitted_at"),
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
    def identity_key(self) -> tuple[UUID, UUID, UUID]:
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
        _uuid(tenant_id, "tenant_id")
        _uuid(lead_id, "lead_id")

        if (
            self.tenant_id != tenant_id
            or self.lead_id != lead_id
        ):
            raise FraudDetectionScopeError(
                "Lead submission observation scope violation"
            )


@dataclass(frozen=True, slots=True)
class VisitTelemetryObservation:
    """Evidence-backed site-visit telemetry observation."""

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
        _uuid(self.observation_id, "observation_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.lead_id, "lead_id")

        object.__setattr__(
            self,
            "observed_at",
            _time(self.observed_at, "observed_at"),
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

        if (
            self.speed_kmh is not None
            and (
                not isinstance(self.speed_kmh, (int, float))
                or isinstance(self.speed_kmh, bool)
                or self.speed_kmh < 0
            )
        ):
            raise FraudDetectionValidationError(
                "speed_kmh must be non-negative number"
            )

    def ensure_scope(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> None:
        _uuid(tenant_id, "tenant_id")
        _uuid(lead_id, "lead_id")

        if (
            self.tenant_id != tenant_id
            or self.lead_id != lead_id
        ):
            raise FraudDetectionScopeError(
                "Visit telemetry scope violation"
            )


@dataclass(frozen=True, slots=True)
class FraudFinding:
    """Immutable, evidence-linked fraud finding."""

    finding_id: UUID
    tenant_id: UUID
    subject_id: UUID
    code: FraudFindingCode
    severity: FraudSeverity
    message: str
    evidence_references: tuple[str, ...]
    source_references: tuple[str, ...]
    observed_at: datetime

    def __post_init__(self) -> None:
        _uuid(self.finding_id, "finding_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.subject_id, "subject_id")

        if not isinstance(
            self.code,
            FraudFindingCode,
        ):
            raise FraudDetectionValidationError(
                "code must be FraudFindingCode"
            )

        if not isinstance(
            self.severity,
            FraudSeverity,
        ):
            raise FraudDetectionValidationError(
                "severity must be FraudSeverity"
            )

        object.__setattr__(
            self,
            "message",
            _text(self.message, "message"),
        )

        object.__setattr__(
            self,
            "evidence_references",
            _references(
                self.evidence_references,
                "evidence_reference",
            ),
        )

        object.__setattr__(
            self,
            "source_references",
            _references(
                self.source_references,
                "source_reference",
            ),
        )

        object.__setattr__(
            self,
            "observed_at",
            _time(self.observed_at, "observed_at"),
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": str(self.tenant_id),
            "subject_id": str(self.subject_id),
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "evidence_references": self.evidence_references,
            "source_references": self.source_references,
            "observed_at": self.observed_at.isoformat(),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "finding_id": str(self.finding_id),
            "tenant_id": str(self.tenant_id),
            "subject_id": str(self.subject_id),
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "evidence_references": list(
                self.evidence_references
            ),
            "source_references": list(
                self.source_references
            ),
            "observed_at": self.observed_at.isoformat(),
            "fingerprint": self.fingerprint,
        }


_HANDOFF_CODE_BY_REASON = {
    FraudHandoffReason.DUPLICATE_LEAD:
        FraudFindingCode.HANDOFF_DUPLICATE_LEAD,
    FraudHandoffReason.ATTRIBUTION_CONFLICT:
        FraudFindingCode.HANDOFF_ATTRIBUTION_CONFLICT,
    FraudHandoffReason.OWNERSHIP_CONFLICT:
        FraudFindingCode.HANDOFF_OWNERSHIP_CONFLICT,
    FraudHandoffReason.IDENTITY_REUSE:
        FraudFindingCode.HANDOFF_IDENTITY_REUSE,
    FraudHandoffReason.EVIDENCE_CONFLICT:
        FraudFindingCode.HANDOFF_EVIDENCE_CONFLICT,
    FraudHandoffReason.SUSPICIOUS_MUTATION:
        FraudFindingCode.HANDOFF_SUSPICIOUS_MUTATION,
}


_HANDOFF_SEVERITY_BY_PRIORITY = {
    FraudHandoffPriority.INFORMATIONAL:
        FraudSeverity.INFORMATIONAL,
    FraudHandoffPriority.REVIEW:
        FraudSeverity.REVIEW,
    FraudHandoffPriority.HIGH:
        FraudSeverity.HIGH,
    FraudHandoffPriority.CRITICAL:
        FraudSeverity.CRITICAL,
}


@dataclass(frozen=True, slots=True)
class FraudAssessment:
    """Immutable fraud assessment result."""

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

    def __post_init__(self) -> None:
        _uuid(self.assessment_id, "assessment_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.subject_id, "subject_id")

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

        if not isinstance(self.findings, tuple):
            raise FraudDetectionValidationError(
                "findings must be tuple"
            )

        for finding in self.findings:
            if not isinstance(
                finding,
                FraudFinding,
            ):
                raise FraudDetectionValidationError(
                    "findings must contain FraudFinding"
                )

            if (
                finding.tenant_id != self.tenant_id
                or finding.subject_id != self.subject_id
            ):
                raise FraudDetectionScopeError(
                    "Finding scope does not match assessment"
                )

        object.__setattr__(
            self,
            "generated_at",
            _time(
                self.generated_at,
                "generated_at",
            ),
        )

        if self.source_of_truth != "fraud_detection":
            raise FraudDetectionValidationError(
                "source_of_truth must be fraud_detection"
            )

    @property
    def identity_key(self) -> tuple[UUID, UUID, str]:
        return (
            self.tenant_id,
            self.subject_id,
            self.correlation_id,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": str(self.tenant_id),
            "subject_id": str(self.subject_id),
            "correlation_id": self.correlation_id,
            "model_version": self.model_version,
            "policy_fingerprint": self.policy_fingerprint,
            "findings": tuple(
                finding.fingerprint
                for finding in self.findings
            ),
            "tripwire_raised": self.tripwire_raised,
            "source_of_truth": self.source_of_truth,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def assert_compatible(
        self,
        other: "FraudAssessment",
    ) -> None:
        if not isinstance(
            other,
            FraudAssessment,
        ):
            raise FraudDetectionValidationError(
                "other must be FraudAssessment"
            )

        if self.identity_key != other.identity_key:
            raise FraudDetectionConflictError(
                "Assessment identities differ"
            )

        if self.fingerprint != other.fingerprint:
            raise FraudDetectionConflictError(
                "Same correlation identity has conflicting fraud result"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "assessment_id": str(self.assessment_id),
            "tenant_id": str(self.tenant_id),
            "subject_id": str(self.subject_id),
            "correlation_id": self.correlation_id,
            "model_version": self.model_version,
            "policy_fingerprint": self.policy_fingerprint,
            "findings": [
                finding.to_dict()
                for finding in self.findings
            ],
            "tripwire_raised": self.tripwire_raised,
            "generated_at": self.generated_at.isoformat(),
            "source_of_truth": self.source_of_truth,
            "fingerprint": self.fingerprint,
        }


class FraudDetectionEngine:
    """ARCH-016 bounded fraud detection authority."""

    def detect(
        self,
        *,
        tenant_id: UUID,
        subject_id: UUID,
        correlation_id: str,
        handoffs: tuple[LeadFraudHandoff, ...] = (),
        submissions: tuple[LeadSubmissionObservation, ...] = (),
        visit_observations: tuple[
            VisitTelemetryObservation, ...
        ] = (),
        policy: FraudDetectionPolicy | None = None,
        assessment_id: UUID | None = None,
        generated_at: datetime | None = None,
    ) -> FraudAssessment:
        _uuid(tenant_id, "tenant_id")
        _uuid(subject_id, "subject_id")
        correlation_id = _text(
            correlation_id,
            "correlation_id",
        )

        policy = policy or FraudDetectionPolicy()

        for handoff in handoffs:
            if not isinstance(
                handoff,
                LeadFraudHandoff,
            ):
                raise FraudDetectionValidationError(
                    "handoffs must contain LeadFraudHandoff"
                )

            handoff.ensure_tenant(tenant_id)

            if handoff.lead_id != subject_id:
                raise FraudDetectionScopeError(
                    "Fraud handoff does not match assessment subject"
                )

        for observation in submissions:
            if not isinstance(
                observation,
                LeadSubmissionObservation,
            ):
                raise FraudDetectionValidationError(
                    "submissions must contain LeadSubmissionObservation"
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
                    "VisitTelemetryObservation"
                )

            observation.ensure_scope(
                tenant_id=tenant_id,
                lead_id=subject_id,
            )

        findings: list[FraudFinding] = []

        findings.extend(
            self._handoff_findings(
                handoffs=handoffs,
                tenant_id=tenant_id,
                subject_id=subject_id,
            )
        )

        velocity_finding = self._velocity_finding(
            submissions=submissions,
            tenant_id=tenant_id,
            subject_id=subject_id,
            policy=policy,
        )

        if velocity_finding is not None:
            findings.append(velocity_finding)

        findings.extend(
            self._telemetry_findings(
                visit_observations=visit_observations,
                tenant_id=tenant_id,
                subject_id=subject_id,
                policy=policy,
            )
        )

        findings = sorted(
            findings,
            key=lambda finding: (
                finding.code.value,
                finding.severity.value,
                finding.observed_at,
                finding.evidence_references,
            ),
        )

        immutable_findings = tuple(findings)

        tripwire_raised = any(
            finding.severity
            in {
                FraudSeverity.HIGH,
                FraudSeverity.CRITICAL,
            }
            for finding in immutable_findings
        )

        return FraudAssessment(
            assessment_id=assessment_id or uuid4(),
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            model_version=FRAUD_DETECTION_MODEL_VERSION,
            policy_fingerprint=policy.fingerprint,
            findings=immutable_findings,
            tripwire_raised=tripwire_raised,
            generated_at=(
                generated_at
                or datetime.now(timezone.utc)
            ),
        )

    def _handoff_findings(
        self,
        *,
        handoffs: tuple[LeadFraudHandoff, ...],
        tenant_id: UUID,
        subject_id: UUID,
    ) -> list[FraudFinding]:
        results: list[FraudFinding] = []

        seen: dict[
            tuple[UUID, UUID, str],
            LeadFraudHandoff,
        ] = {}

        for handoff in handoffs:
            existing = seen.get(handoff.handoff_key)

            if existing is not None:
                existing.assert_compatible(handoff)
                continue

            seen[handoff.handoff_key] = handoff

            results.append(
                FraudFinding(
                    finding_id=uuid4(),
                    tenant_id=tenant_id,
                    subject_id=subject_id,
                    code=_HANDOFF_CODE_BY_REASON[
                        handoff.reason
                    ],
                    severity=_HANDOFF_SEVERITY_BY_PRIORITY[
                        handoff.priority
                    ],
                    message=(
                        "CORE-003 fraud handoff received: "
                        f"{handoff.reason.value}"
                    ),
                    evidence_references=(
                        handoff.evidence_references
                    ),
                    source_references=(
                        (handoff.source_reference,)
                    ),
                    observed_at=handoff.created_at,
                )
            )

        return results

    def _velocity_finding(
        self,
        *,
        submissions: tuple[LeadSubmissionObservation, ...],
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
            if window_start
            <= item.submitted_at
            <= latest.submitted_at
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
            code=FraudFindingCode.LEAD_SUBMISSION_VELOCITY,
            severity=FraudSeverity.HIGH,
            message=(
                "Lead submission velocity exceeded the configured "
                "fraud-detection threshold."
            ),
            evidence_references=tuple(
                item.evidence_reference
                for item in windowed
            ),
            source_references=tuple(
                dict.fromkeys(
                    item.source_reference
                    for item in windowed
                )
            ),
            observed_at=latest.submitted_at,
        )

    def _telemetry_findings(
        self,
        *,
        visit_observations: tuple[
            VisitTelemetryObservation, ...
        ],
        tenant_id: UUID,
        subject_id: UUID,
        policy: FraudDetectionPolicy,
    ) -> list[FraudFinding]:
        results: list[FraudFinding] = []

        for observation in visit_observations:
            if observation.mock_location_provider:
                results.append(
                    FraudFinding(
                        finding_id=uuid4(),
                        tenant_id=tenant_id,
                        subject_id=subject_id,
                        code=FraudFindingCode.GPS_MOCK_LOCATION,
                        severity=FraudSeverity.CRITICAL,
                        message=(
                            "Site-visit telemetry reports a "
                            "mock-location provider."
                        ),
                        evidence_references=(
                            observation.evidence_reference,
                        ),
                        source_references=(
                            observation.source_reference,
                        ),
                        observed_at=observation.observed_at,
                    )
                )

            if observation.proxy_detected:
                results.append(
                    FraudFinding(
                        finding_id=uuid4(),
                        tenant_id=tenant_id,
                        subject_id=subject_id,
                        code=FraudFindingCode.GPS_PROXY_DETECTED,
                        severity=FraudSeverity.HIGH,
                        message=(
                            "Site-visit telemetry reports proxy "
                            "or anonymizing-network indicators."
                        ),
                        evidence_references=(
                            observation.evidence_reference,
                        ),
                        source_references=(
                            observation.source_reference,
                        ),
                        observed_at=observation.observed_at,
                    )
                )

            if (
                observation.speed_kmh is not None
                and observation.speed_kmh
                > policy.max_plausible_speed_kmh
            ):
                results.append(
                    FraudFinding(
                        finding_id=uuid4(),
                        tenant_id=tenant_id,
                        subject_id=subject_id,
                        code=(
                            FraudFindingCode.GPS_IMPOSSIBLE_SPEED
                        ),
                        severity=FraudSeverity.HIGH,
                        message=(
                            "Site-visit telemetry exceeds the "
                            "configured plausible travel-speed "
                            "threshold."
                        ),
                        evidence_references=(
                            observation.evidence_reference,
                        ),
                        source_references=(
                            observation.source_reference,
                        ),
                        observed_at=observation.observed_at,
                    )
                )

        return results