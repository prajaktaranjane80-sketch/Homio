from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from ..lead_ownership.lead_fraud_handoff import (
    FraudHandoffConflictError,
    FraudHandoffPriority,
    FraudHandoffReason,
    LeadFraudHandoff,
)

from .fraud_detection import (
    FRAUD_DETECTION_MODEL_VERSION,
    FraudAssessment,
    FraudDetectionConflictError,
    FraudDetectionEngine,
    FraudDetectionPolicy,
    FraudDetectionScopeError,
    FraudDetectionValidationError,
    FraudFindingCode,
    FraudSeverity,
    LeadSubmissionObservation,
    VisitTelemetryObservation,
)


TENANT = UUID("11111111-1111-1111-1111-111111111111")
OTHER_TENANT = UUID("22222222-2222-2222-2222-222222222222")
LEAD = UUID("33333333-3333-3333-3333-333333333333")
NOW = datetime(
    2026,
    9,
    29,
    12,
    0,
    tzinfo=timezone.utc,
)


def make_submission(
    *,
    seconds: int,
    tenant_id: UUID = TENANT,
    lead_id: UUID = LEAD,
    suffix: str | None = None,
) -> LeadSubmissionObservation:
    suffix = suffix or str(seconds)

    return LeadSubmissionObservation(
        submission_id=uuid4(),
        tenant_id=tenant_id,
        lead_id=lead_id,
        submitted_at=NOW + timedelta(seconds=seconds),
        evidence_reference=f"evidence:submission:{suffix}",
        source_reference="core003:lead_ingestion",
    )


def make_visit(
    *,
    mock: bool = False,
    proxy: bool = False,
    speed_kmh: float | None = None,
    tenant_id: UUID = TENANT,
    lead_id: UUID = LEAD,
) -> VisitTelemetryObservation:
    return VisitTelemetryObservation(
        observation_id=uuid4(),
        tenant_id=tenant_id,
        lead_id=lead_id,
        observed_at=NOW,
        evidence_reference="evidence:visit:001",
        source_reference="core014:visit-telemetry",
        mock_location_provider=mock,
        proxy_detected=proxy,
        speed_kmh=speed_kmh,
    )


def test_policy_is_immutable_and_fingerprinted() -> None:
    policy = FraudDetectionPolicy()

    assert policy.version == FRAUD_DETECTION_MODEL_VERSION
    assert policy.fingerprint

    with pytest.raises(AttributeError):
        policy.version = "2.0"  # type: ignore[misc]


def test_invalid_policy_is_rejected() -> None:
    with pytest.raises(FraudDetectionValidationError):
        FraudDetectionPolicy(velocity_window_seconds=0)

    with pytest.raises(FraudDetectionValidationError):
        FraudDetectionPolicy(max_submissions_in_window=0)

    with pytest.raises(FraudDetectionValidationError):
        FraudDetectionPolicy(max_plausible_speed_kmh=0)


def test_empty_observation_set_is_clear_and_no_tripwire() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="assessment-001",
    )

    assert assessment.findings == ()
    assert assessment.tripwire_raised is False


def test_velocity_detection_raises_high_tripwire() -> None:
    submissions = tuple(
        make_submission(seconds=index)
        for index in range(4)
    )

    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="velocity-001",
        submissions=submissions,
    )

    codes = {
        finding.code
        for finding in assessment.findings
    }

    assert FraudFindingCode.LEAD_SUBMISSION_VELOCITY in codes
    assert assessment.tripwire_raised is True


def test_velocity_threshold_is_inclusive_of_window() -> None:
    policy = FraudDetectionPolicy(
        velocity_window_seconds=60,
        max_submissions_in_window=3,
    )

    submissions = (
        make_submission(seconds=0),
        make_submission(seconds=20),
        make_submission(seconds=40),
        make_submission(seconds=70),
    )

    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="velocity-window-001",
        submissions=submissions,
        policy=policy,
    )

    assert assessment.findings == ()


def test_velocity_detection_is_order_independent() -> None:
    submissions = (
        make_submission(seconds=0),
        make_submission(seconds=1),
        make_submission(seconds=2),
        make_submission(seconds=3),
    )

    first = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="velocity-order-001",
        submissions=submissions,
    )

    second = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="velocity-order-001",
        submissions=tuple(reversed(submissions)),
    )

    assert [f.code for f in first.findings] == [
        f.code for f in second.findings
    ]
    assert first.tripwire_raised == second.tripwire_raised


def test_mock_location_is_critical_tripwire() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="gps-mock-001",
        visit_observations=(
            make_visit(mock=True),
        ),
    )

    assert assessment.findings[0].code == (
        FraudFindingCode.GPS_MOCK_LOCATION
    )
    assert assessment.findings[0].severity == FraudSeverity.CRITICAL
    assert assessment.tripwire_raised is True


def test_proxy_detection_is_high_tripwire() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="gps-proxy-001",
        visit_observations=(
            make_visit(proxy=True),
        ),
    )

    assert assessment.findings[0].code == (
        FraudFindingCode.GPS_PROXY_DETECTED
    )
    assert assessment.findings[0].severity == FraudSeverity.HIGH
    assert assessment.tripwire_raised is True


def test_impossible_speed_detection_is_high_tripwire() -> None:
    policy = FraudDetectionPolicy(
        max_plausible_speed_kmh=180,
    )

    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="gps-speed-001",
        visit_observations=(
            make_visit(speed_kmh=181),
        ),
        policy=policy,
    )

    assert assessment.findings[0].code == (
        FraudFindingCode.GPS_IMPOSSIBLE_SPEED
    )
    assert assessment.tripwire_raised is True


def test_normal_telemetry_does_not_trigger_tripwire() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="gps-clean-001",
        visit_observations=(
            make_visit(speed_kmh=90),
        ),
    )

    assert assessment.findings == ()
    assert assessment.tripwire_raised is False


def test_cross_tenant_submission_is_rejected() -> None:
    submission = make_submission(
        seconds=0,
        tenant_id=OTHER_TENANT,
    )

    with pytest.raises(FraudDetectionScopeError):
        FraudDetectionEngine().detect(
            tenant_id=TENANT,
            subject_id=LEAD,
            correlation_id="scope-001",
            submissions=(submission,),
        )


def test_cross_subject_submission_is_rejected() -> None:
    other_lead = uuid4()
    submission = make_submission(
        seconds=0,
        lead_id=other_lead,
    )

    with pytest.raises(FraudDetectionScopeError):
        FraudDetectionEngine().detect(
            tenant_id=TENANT,
            subject_id=LEAD,
            correlation_id="scope-002",
            submissions=(submission,),
        )


def test_submission_requires_evidence_reference() -> None:
    with pytest.raises(FraudDetectionValidationError):
        LeadSubmissionObservation(
            submission_id=uuid4(),
            tenant_id=TENANT,
            lead_id=LEAD,
            submitted_at=NOW,
            evidence_reference="",
            source_reference="source:001",
        )


def test_visit_requires_source_reference() -> None:
    with pytest.raises(FraudDetectionValidationError):
        VisitTelemetryObservation(
            observation_id=uuid4(),
            tenant_id=TENANT,
            lead_id=LEAD,
            observed_at=NOW,
            evidence_reference="evidence:001",
            source_reference="",
        )


def test_assessment_is_immutable_and_serializable() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="serialize-001",
    )

    assert isinstance(assessment, FraudAssessment)
    payload = assessment.to_dict()

    assert payload["tenant_id"] == str(TENANT)
    assert payload["subject_id"] == str(LEAD)
    assert payload["source_of_truth"] == "fraud_detection"
    assert "fingerprint" in payload

    with pytest.raises(AttributeError):
        assessment.tripwire_raised = True  # type: ignore[misc]


def test_same_assessment_identity_accepts_compatible_result() -> None:
    engine = FraudDetectionEngine()

    first = engine.detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="compatible-001",
        assessment_id=UUID(
            "44444444-4444-4444-4444-444444444444"
        ),
        generated_at=NOW,
    )

    second = engine.detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="compatible-001",
        assessment_id=UUID(
            "55555555-5555-5555-5555-555555555555"
        ),
        generated_at=NOW + timedelta(seconds=5),
    )

    first.assert_compatible(second)


def test_same_assessment_identity_rejects_conflicting_result() -> None:
    engine = FraudDetectionEngine()

    first = engine.detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="conflict-001",
        generated_at=NOW,
    )

    second = engine.detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="conflict-001",
        visit_observations=(
            make_visit(mock=True),
        ),
        generated_at=NOW,
    )

    with pytest.raises(FraudDetectionConflictError):
        first.assert_compatible(second)


def test_source_of_truth_is_not_authorization() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="boundary-001",
    )

    payload = assessment.to_dict()

    assert "allowed" not in payload
    assert "requires_approval" not in payload
    assert "authorization" not in payload
    assert "policy_decision" not in payload


def test_model_version_is_explicit() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="version-001",
    )

    assert assessment.model_version == FRAUD_DETECTION_MODEL_VERSION


def test_finding_evidence_is_preserved() -> None:
    assessment = FraudDetectionEngine().detect(
        tenant_id=TENANT,
        subject_id=LEAD,
        correlation_id="evidence-001",
        visit_observations=(
            make_visit(
                mock=True,
                proxy=True,
            ),
        ),
    )

    assert len(assessment.findings) == 2

    for finding in assessment.findings:
        assert finding.evidence_references
        assert finding.source_references
        assert finding.fingerprint


def test_negative_speed_is_rejected() -> None:
    with pytest.raises(FraudDetectionValidationError):
        make_visit(speed_kmh=-1)


def test_negative_velocity_configuration_is_rejected() -> None:
    with pytest.raises(FraudDetectionValidationError):
        FraudDetectionPolicy(
            velocity_window_seconds=-1
        )
def test_conflicting_same_handoff_identity_is_rejected() -> None:
    first = LeadFraudHandoff.create(
        tenant_id=TENANT,
        lead_id=LEAD,
        reason=FraudHandoffReason.DUPLICATE_LEAD,
        priority=FraudHandoffPriority.HIGH,
        idempotency_key="handoff-conflict-001",
        evidence_references=("evidence:001",),
        source_reference="core003:test",
        created_at=NOW,
    )

    conflicting = LeadFraudHandoff.create(
        tenant_id=TENANT,
        lead_id=LEAD,
        reason=FraudHandoffReason.OWNERSHIP_CONFLICT,
        priority=FraudHandoffPriority.HIGH,
        idempotency_key="handoff-conflict-001",
        evidence_references=("evidence:001",),
        source_reference="core003:test",
        created_at=NOW,
    )

    with pytest.raises(FraudHandoffConflictError):
        FraudDetectionEngine().detect(
            tenant_id=TENANT,
            subject_id=LEAD,
            correlation_id="handoff-conflict-001",
            handoffs=(first, conflicting),
        )