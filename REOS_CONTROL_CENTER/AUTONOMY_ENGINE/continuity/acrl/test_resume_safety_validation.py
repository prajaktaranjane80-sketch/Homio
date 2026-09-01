"""ACRL T12 — Resume-Safety Validation tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.resume_safety_validation import (
    ResumeDecision,
    ResumeSafetyAuthorityError,
    ResumeSafetyBlockedError,
    ResumeSafetyIntegrityError,
    ResumeSafetyReason,
    ResumeSafetyRequest,
    ResumeSafetyReport,
    ResumeSafetyValidationError,
    ResumeSafetyValidator,
    is_safe_to_resume,
    validate_resume_safety,
)


def make_request(
    *,
    checkpoint_available: bool = True,
    checkpoint_valid: bool = True,
    state_available: bool = True,
    state_valid: bool = True,
    gate_available: bool = True,
    gate_valid: bool = True,
    authority_valid: bool = True,
    integrity_valid: bool = True,
    architecture_stable: bool = True,
    recovery_safe: bool = True,
    state_ambiguous: bool = False,
    state_stale: bool = False,
) -> ResumeSafetyRequest:
    return ResumeSafetyRequest(
        checkpoint_available=checkpoint_available,
        checkpoint_valid=checkpoint_valid,
        state_available=state_available,
        state_valid=state_valid,
        gate_available=gate_available,
        gate_valid=gate_valid,
        authority_valid=authority_valid,
        integrity_valid=integrity_valid,
        architecture_stable=architecture_stable,
        recovery_safe=recovery_safe,
        state_ambiguous=state_ambiguous,
        state_stale=state_stale,
    )


def test_valid_resume_is_safe() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert (
        report.decision
        == ResumeDecision.SAFE_TO_RESUME
    )


def test_valid_resume_reason_is_valid() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert (
        report.reason
        == ResumeSafetyReason.VALID
    )


def test_valid_resume_is_not_fail_closed() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert report.fail_closed is False


def test_valid_resume_is_validated() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert report.validated is True


def test_missing_checkpoint_blocks_resume() -> None:
    report = validate_resume_safety(
        make_request(
            checkpoint_available=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.BLOCK_RESUME
    )

    assert (
        report.reason
        == ResumeSafetyReason.MISSING_CHECKPOINT
    )


def test_invalid_checkpoint_fails_closed() -> None:
    report = validate_resume_safety(
        make_request(
            checkpoint_valid=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == ResumeSafetyReason.CHECKPOINT_INVALID
    )


def test_missing_state_blocks_resume() -> None:
    report = validate_resume_safety(
        make_request(
            state_available=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.BLOCK_RESUME
    )

    assert (
        report.reason
        == ResumeSafetyReason.STATE_INVALID
    )


def test_invalid_state_fails_closed() -> None:
    report = validate_resume_safety(
        make_request(
            state_valid=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.FAIL_CLOSED
    )


def test_missing_gate_blocks_resume() -> None:
    report = validate_resume_safety(
        make_request(
            gate_available=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.BLOCK_RESUME
    )

    assert (
        report.reason
        == ResumeSafetyReason.GATE_INVALID
    )


def test_invalid_gate_fails_closed() -> None:
    report = validate_resume_safety(
        make_request(
            gate_valid=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == ResumeSafetyReason.GATE_INVALID
    )


def test_invalid_authority_is_rejected() -> None:
    with pytest.raises(
        ResumeSafetyAuthorityError
    ):
        validate_resume_safety(
            make_request(
                authority_valid=False
            )
        )


def test_invalid_integrity_is_rejected() -> None:
    with pytest.raises(
        ResumeSafetyIntegrityError
    ):
        validate_resume_safety(
            make_request(
                integrity_valid=False
            )
        )


def test_architecture_drift_fails_closed() -> None:
    report = validate_resume_safety(
        make_request(
            architecture_stable=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == ResumeSafetyReason.ARCHITECTURE_DRIFT
    )


def test_ambiguous_state_fails_closed() -> None:
    report = validate_resume_safety(
        make_request(
            state_ambiguous=True
        )
    )

    assert (
        report.decision
        == ResumeDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == ResumeSafetyReason.AMBIGUOUS_STATE
    )


def test_unsafe_recovery_blocks_resume() -> None:
    report = validate_resume_safety(
        make_request(
            recovery_safe=False
        )
    )

    assert (
        report.decision
        == ResumeDecision.BLOCK_RESUME
    )

    assert (
        report.reason
        == ResumeSafetyReason.RECOVERY_UNSAFE
    )


def test_stale_state_blocks_resume() -> None:
    report = validate_resume_safety(
        make_request(
            state_stale=True
        )
    )

    assert (
        report.decision
        == ResumeDecision.BLOCK_RESUME
    )

    assert (
        report.reason
        == ResumeSafetyReason.STALE_STATE
    )


def test_safe_resume_helper_returns_true() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert (
        is_safe_to_resume(report)
        is True
    )


def test_blocked_resume_helper_returns_false() -> None:
    report = validate_resume_safety(
        make_request(
            checkpoint_available=False
        )
    )

    assert (
        is_safe_to_resume(report)
        is False
    )


def test_fail_closed_helper_returns_false() -> None:
    report = validate_resume_safety(
        make_request(
            architecture_stable=False
        )
    )

    assert (
        is_safe_to_resume(report)
        is False
    )


def test_validate_or_raise_accepts_safe_resume() -> None:
    report = (
        ResumeSafetyValidator.validate_or_raise(
            make_request()
        )
    )

    assert (
        report.decision
        == ResumeDecision.SAFE_TO_RESUME
    )


def test_validate_or_raise_blocks_missing_checkpoint() -> None:
    with pytest.raises(
        ResumeSafetyBlockedError
    ):
        ResumeSafetyValidator.validate_or_raise(
            make_request(
                checkpoint_available=False
            )
        )


def test_validate_or_raise_blocks_unsafe_recovery() -> None:
    with pytest.raises(
        ResumeSafetyBlockedError
    ):
        ResumeSafetyValidator.validate_or_raise(
            make_request(
                recovery_safe=False
            )
        )


def test_fingerprint_is_deterministic() -> None:
    request = make_request()

    first = ResumeSafetyValidator.fingerprint(
        request.to_dict()
    )

    second = ResumeSafetyValidator.fingerprint(
        request.to_dict()
    )

    assert first == second


def test_fingerprint_has_sha256_length() -> None:
    fingerprint = ResumeSafetyValidator.fingerprint(
        {"resume": "test"}
    )

    assert len(fingerprint) == 64


def test_request_serializes() -> None:
    request = make_request()

    data = request.to_dict()

    assert data["checkpoint_available"] is True
    assert data["state_available"] is True
    assert data["gate_available"] is True
    assert data["authority_valid"] is True


def test_report_serializes() -> None:
    report = validate_resume_safety(
        make_request()
    )

    data = report.to_dict()

    assert data["schema_version"] == "1.0"
    assert (
        data["authority"]
        == "REOS_CONTROL_CENTER"
    )
    assert data["decision"] == (
        "SAFE_TO_RESUME"
    )


def test_report_contains_fingerprint() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert len(
        report.request_fingerprint
    ) == 64


def test_report_is_machine_readable() -> None:
    report = validate_resume_safety(
        make_request()
    )

    data = report.to_dict()

    assert isinstance(data, dict)
    assert isinstance(
        data["decision"],
        str,
    )
    assert isinstance(
        data["reason"],
        str,
    )


def test_invalid_request_type_is_rejected() -> None:
    with pytest.raises(
        ResumeSafetyValidationError
    ):
        validate_resume_safety(
            object()
        )


def test_safe_resume_requires_all_core_conditions() -> None:
    fields = [
        "checkpoint_valid",
        "state_valid",
        "gate_valid",
        "architecture_stable",
        "recovery_safe",
    ]

    for field in fields:
        kwargs = {
            field: False,
        }

        report = validate_resume_safety(
            make_request(**kwargs)
        )

        assert (
            report.decision
            != ResumeDecision.SAFE_TO_RESUME
        )


def test_safe_resume_requires_checkpoint() -> None:
    report = validate_resume_safety(
        make_request(
            checkpoint_available=False
        )
    )

    assert (
        report.decision
        != ResumeDecision.SAFE_TO_RESUME
    )


def test_safe_resume_requires_state() -> None:
    report = validate_resume_safety(
        make_request(
            state_available=False
        )
    )

    assert (
        report.decision
        != ResumeDecision.SAFE_TO_RESUME
    )


def test_safe_resume_requires_gate() -> None:
    report = validate_resume_safety(
        make_request(
            gate_available=False
        )
    )

    assert (
        report.decision
        != ResumeDecision.SAFE_TO_RESUME
    )


def test_safe_resume_requires_recovery_safety() -> None:
    report = validate_resume_safety(
        make_request(
            recovery_safe=False
        )
    )

    assert (
        report.decision
        != ResumeDecision.SAFE_TO_RESUME
    )


def test_schema_version_is_fixed() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert report.schema_version == "1.0"


def test_authority_is_fixed() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert (
        report.authority
        == "REOS_CONTROL_CENTER"
    )


def test_algorithm_is_sha256() -> None:
    assert (
        ResumeSafetyValidator.ALGORITHM
        == "sha256"
    )


def test_state_ambiguity_has_precedence() -> None:
    report = validate_resume_safety(
        make_request(
            state_ambiguous=True,
            state_stale=True,
        )
    )

    assert (
        report.reason
        == ResumeSafetyReason.AMBIGUOUS_STATE
    )


def test_architecture_drift_has_precedence() -> None:
    report = validate_resume_safety(
        make_request(
            architecture_stable=False,
            recovery_safe=False,
        )
    )

    assert (
        report.reason
        == ResumeSafetyReason.ARCHITECTURE_DRIFT
    )


def test_checkpoint_failure_has_precedence_over_state() -> None:
    report = validate_resume_safety(
        make_request(
            checkpoint_valid=False,
            state_valid=False,
        )
    )

    assert (
        report.reason
        == ResumeSafetyReason.CHECKPOINT_INVALID
    )


def test_gate_failure_is_fail_closed() -> None:
    report = validate_resume_safety(
        make_request(
            gate_valid=False
        )
    )

    assert report.fail_closed is True


def test_missing_checkpoint_is_not_fail_closed() -> None:
    report = validate_resume_safety(
        make_request(
            checkpoint_available=False
        )
    )

    assert report.fail_closed is False


def test_safe_resume_has_no_failure_reason() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert (
        report.reason
        == ResumeSafetyReason.VALID
    )


def test_safe_resume_report_has_no_failure_state() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert report.fail_closed is False
    assert report.validated is True


def test_report_type_is_correct() -> None:
    report = validate_resume_safety(
        make_request()
    )

    assert isinstance(
        report,
        ResumeSafetyReport,
    )


def test_resume_decision_values_are_stable() -> None:
    assert (
        ResumeDecision.SAFE_TO_RESUME.value
        == "SAFE_TO_RESUME"
    )

    assert (
        ResumeDecision.BLOCK_RESUME.value
        == "BLOCK_RESUME"
    )

    assert (
        ResumeDecision.FAIL_CLOSED.value
        == "FAIL_CLOSED"
    )