"""ACRL T13 — Controller Integration tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationAuthorityError,
    ControllerIntegrationConflictError,
    ControllerIntegrationEngine,
    ControllerIntegrationRequest,
    ControllerIntegrationValidationError,
    ControllerStateView,
    IntegrationDecision,
    IntegrationReason,
    controller_resume_authorized,
    integrate_controller,
)


def make_controller(
    *,
    gate: str = "CORE-004",
    subtask: str | None = "CORE-004-T01",
    task: str = "Implement project domain.",
    status: str = "CONTROL_CENTER_DRIVEN",
    architecture_locked: bool = True,
    authoritative: bool = True,
    checkpoint_id: str | None = "CP-00001",
) -> ControllerStateView:
    return ControllerStateView(
        current_gate=gate,
        current_subtask=subtask,
        current_task=task,
        status=status,
        state_hash="controller-hash",
        architecture_locked=architecture_locked,
        authoritative=authoritative,
        checkpoint_id=checkpoint_id,
    )


def make_acrl(
    *,
    gate: str = "CORE-004",
    subtask: str | None = "CORE-004-T01",
    task: str | None = "Implement project domain.",
    checkpoint_id: str | None = "CP-00001",
    architecture_locked: bool = True,
    authority_valid: bool = True,
    integrity_valid: bool = True,
    resume_safe: bool = True,
) -> ACRLContinuityView:
    return ACRLContinuityView(
        current_gate=gate,
        current_subtask=subtask,
        current_task=task,
        checkpoint_id=checkpoint_id,
        architecture_locked=architecture_locked,
        authority_valid=authority_valid,
        integrity_valid=integrity_valid,
        resume_safe=resume_safe,
        fingerprint="acrl-fingerprint",
    )


def make_request(**kwargs) -> ControllerIntegrationRequest:
    controller_kwargs = {}
    acrl_kwargs = {}

    controller_fields = {
        "gate",
        "subtask",
        "task",
        "status",
        "architecture_locked",
        "authoritative",
        "checkpoint_id",
    }

    acrl_fields = {
        "gate",
        "subtask",
        "task",
        "checkpoint_id",
        "architecture_locked",
        "authority_valid",
        "integrity_valid",
        "resume_safe",
    }

    controller_values = {
        key: value
        for key, value in kwargs.items()
        if key in controller_fields
    }

    acrl_values = {
        key: value
        for key, value in kwargs.items()
        if key in acrl_fields
    }

    controller_kwargs = controller_values
    acrl_kwargs = acrl_values

    return ControllerIntegrationRequest(
        controller=make_controller(
            **controller_kwargs
        ),
        acrl=make_acrl(
            **acrl_kwargs
        ),
    )


def test_valid_controller_integration() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        report.decision
        == IntegrationDecision.INTEGRATED
    )


def test_valid_integration_reason() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        report.reason
        == IntegrationReason.VALID
    )


def test_valid_integration_authorizes_resume() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.resume_authorized is True


def test_valid_integration_does_not_authorize_execution() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.execution_authorized is False


def test_controller_remains_execution_authority() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        report.authority
        == "REOS_CONTROL_CENTER"
    )


def test_gate_conflict_fails_closed() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                gate="CORE-005"
            ),
            acrl=make_acrl(
                gate="CORE-004"
            ),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == IntegrationReason.GATE_CONFLICT
    )

    assert report.fail_closed is True


def test_subtask_conflict_fails_closed() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                subtask="CORE-004-T02"
            ),
            acrl=make_acrl(
                subtask="CORE-004-T01"
            ),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == IntegrationReason.SUBTASK_CONFLICT
    )


def test_checkpoint_conflict_blocks_resume() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                checkpoint_id="CP-00002"
            ),
            acrl=make_acrl(
                checkpoint_id="CP-00001"
            ),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.BLOCKED
    )

    assert (
        report.reason
        == IntegrationReason.CHECKPOINT_CONFLICT
    )


def test_architecture_lock_conflict_fails_closed() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                architecture_locked=True
            ),
            acrl=make_acrl(
                architecture_locked=False
            ),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == IntegrationReason.ARCHITECTURE_CONFLICT
    )


def test_unlocked_architecture_blocks_resume() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                architecture_locked=False
            ),
            acrl=make_acrl(
                architecture_locked=False
            ),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.BLOCKED
    )


def test_authority_conflict_is_rejected() -> None:
    with pytest.raises(
        ControllerIntegrationAuthorityError
    ):
        integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(
                    authoritative=False
                ),
                acrl=make_acrl(),
            )
        )


def test_acrl_authority_conflict_is_rejected() -> None:
    with pytest.raises(
        ControllerIntegrationAuthorityError
    ):
        integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(
                    authority_valid=False
                ),
            )
        )


def test_integrity_failure_fails_closed() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(
                integrity_valid=False
            ),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == IntegrationReason.INTEGRITY_CONFLICT
    )


def test_resume_not_safe_blocks() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(
                resume_safe=False
            ),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.BLOCKED
    )

    assert (
        report.reason
        == IntegrationReason.RESUME_NOT_SAFE
    )


def test_invalid_controller_gate_fails_closed() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                gate=""
            ),
            acrl=make_acrl(),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.FAIL_CLOSED
    )


def test_invalid_controller_task_fails_closed() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                task=""
            ),
            acrl=make_acrl(),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.FAIL_CLOSED
    )


def test_unsupported_controller_status_blocks() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                status="PAUSED"
            ),
            acrl=make_acrl(),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.BLOCKED
    )

    assert (
        report.reason
        == IntegrationReason
        .CONTROLLER_STATE_INVALID
    )


def test_ready_for_approval_status_is_integrable() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                status="READY_FOR_APPROVAL"
            ),
            acrl=make_acrl(),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.INTEGRATED
    )


def test_current_status_is_integrable() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                status="CURRENT"
            ),
            acrl=make_acrl(),
        )
    )

    assert (
        report.decision
        == IntegrationDecision.INTEGRATED
    )


def test_resume_authorization_helper() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        controller_resume_authorized(report)
        is True
    )


def test_blocked_report_cannot_resume() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                status="PAUSED"
            ),
            acrl=make_acrl(),
        )
    )

    assert (
        controller_resume_authorized(report)
        is False
    )


def test_fail_closed_report_cannot_resume() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                gate="CORE-005"
            ),
            acrl=make_acrl(
                gate="CORE-004"
            ),
        )
    )

    assert (
        controller_resume_authorized(report)
        is False
    )


def test_report_contains_both_gate_ids() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.controller_gate == "CORE-004"
    assert report.acrl_gate == "CORE-004"


def test_report_contains_both_subtask_ids() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        report.controller_subtask
        == "CORE-004-T01"
    )

    assert (
        report.acrl_subtask
        == "CORE-004-T01"
    )


def test_report_is_validated() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.validated is True


def test_valid_report_is_not_fail_closed() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.fail_closed is False


def test_fingerprint_is_deterministic() -> None:
    request = make_request()

    first = ControllerIntegrationEngine.fingerprint(
        request.to_dict()
    )

    second = ControllerIntegrationEngine.fingerprint(
        request.to_dict()
    )

    assert first == second


def test_fingerprint_is_sha256() -> None:
    request = make_request()

    fingerprint = (
        ControllerIntegrationEngine.fingerprint(
            request.to_dict()
        )
    )

    assert len(fingerprint) == 64


def test_request_serializes() -> None:
    request = make_request()

    data = request.to_dict()

    assert "controller" in data
    assert "acrl" in data
    assert (
        data["expected_authority"]
        == "REOS_CONTROL_CENTER"
    )


def test_report_serializes() -> None:
    report = integrate_controller(
        make_request()
    )

    data = report.to_dict()

    assert data["decision"] == "INTEGRATED"
    assert data["reason"] == "VALID"
    assert (
        data["authority"]
        == "REOS_CONTROL_CENTER"
    )


def test_invalid_request_type_rejected() -> None:
    with pytest.raises(
        ControllerIntegrationValidationError
    ):
        ControllerIntegrationEngine.integrate(
            object()
        )


def test_wrong_expected_authority_rejected() -> None:
    request = ControllerIntegrationRequest(
        controller=make_controller(),
        acrl=make_acrl(),
        expected_authority="OTHER_SYSTEM",
    )

    with pytest.raises(
        ControllerIntegrationAuthorityError
    ):
        integrate_controller(request)


def test_integrate_or_raise_accepts_valid_state() -> None:
    report = (
        ControllerIntegrationEngine.integrate_or_raise(
            make_request()
        )
    )

    assert (
        report.decision
        == IntegrationDecision.INTEGRATED
    )


def test_integrate_or_raise_rejects_conflict() -> None:
    request = ControllerIntegrationRequest(
        controller=make_controller(
            gate="CORE-005"
        ),
        acrl=make_acrl(
            gate="CORE-004"
        ),
    )

    with pytest.raises(
        ControllerIntegrationConflictError
    ):
        ControllerIntegrationEngine.integrate_or_raise(
            request
        )


def test_controller_state_is_not_mutated() -> None:
    controller = make_controller()
    original = controller.to_dict()

    integrate_controller(
        ControllerIntegrationRequest(
            controller=controller,
            acrl=make_acrl(),
        )
    )

    assert controller.to_dict() == original


def test_acrl_state_is_not_mutated() -> None:
    acrl = make_acrl()
    original = acrl.to_dict()

    integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=acrl,
        )
    )

    assert acrl.to_dict() == original


def test_execution_authorization_is_always_false() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.execution_authorized is False


def test_t13_only_authorizes_continuity() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.resume_authorized is True
    assert report.execution_authorized is False


def test_gate_conflict_has_priority_over_resume() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                gate="CORE-005"
            ),
            acrl=make_acrl(
                gate="CORE-004",
                resume_safe=False,
            ),
        )
    )

    assert (
        report.reason
        == IntegrationReason.GATE_CONFLICT
    )


def test_integrity_conflict_has_priority_over_resume() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(
                integrity_valid=False,
                resume_safe=False,
            ),
        )
    )

    assert (
        report.reason
        == IntegrationReason.INTEGRITY_CONFLICT
    )


def test_architecture_conflict_has_priority() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                architecture_locked=True
            ),
            acrl=make_acrl(
                architecture_locked=False,
                resume_safe=False,
            ),
        )
    )

    assert (
        report.reason
        == IntegrationReason.ARCHITECTURE_CONFLICT
    )


def test_checkpoint_conflict_does_not_mutate_state() -> None:
    controller = make_controller(
        checkpoint_id="CP-2"
    )
    acrl = make_acrl(
        checkpoint_id="CP-1"
    )

    controller_before = controller.to_dict()
    acrl_before = acrl.to_dict()

    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=controller,
            acrl=acrl,
        )
    )

    assert (
        report.decision
        == IntegrationDecision.BLOCKED
    )

    assert controller.to_dict() == controller_before
    assert acrl.to_dict() == acrl_before


def test_authoritative_gate_must_match() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        report.controller_gate
        == report.acrl_gate
    )


def test_authoritative_subtask_must_match() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        report.controller_subtask
        == report.acrl_subtask
    )


def test_schema_version_is_stable() -> None:
    report = integrate_controller(
        make_request()
    )

    assert report.schema_version == "1.0"


def test_authority_is_stable() -> None:
    report = integrate_controller(
        make_request()
    )

    assert (
        report.authority
        == "REOS_CONTROL_CENTER"
    )


def test_safe_resume_requires_integrated_decision() -> None:
    report = integrate_controller(
        ControllerIntegrationRequest(
            controller=make_controller(
                status="PAUSED"
            ),
            acrl=make_acrl(),
        )
    )

    assert (
        report.decision
        != IntegrationDecision.INTEGRATED
    )

    assert (
        controller_resume_authorized(report)
        is False
    )


def test_safe_integration_is_idempotent() -> None:
    request = make_request()

    first = integrate_controller(request)
    second = integrate_controller(request)

    assert first.to_dict() == second.to_dict()


def test_no_execution_side_effects() -> None:
    request = make_request()

    report = integrate_controller(request)

    assert report.execution_authorized is False