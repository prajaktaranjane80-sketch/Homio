"""ACRL T13 — Controller Integration adversarial tests."""

import pytest

from .controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationEngine,
    ControllerIntegrationRequest,
    ControllerStateView,
    IntegrationDecision,
    IntegrationReason,
)


def build_request(
    *,
    controller_gate="CORE-005",
    acrl_gate="CORE-005",
    controller_subtask="CORE-005-T01",
    acrl_subtask="CORE-005-T01",
    checkpoint_id="CP-T09-001",
    architecture_locked=True,
    controller_status="CONTROL_CENTER_DRIVEN",
    integrity_valid=True,
    resume_safe=True,
    metadata=None,
):
    controller = ControllerStateView(
        current_gate=controller_gate,
        current_subtask=controller_subtask,
        current_task="Implement controller integration",
        status=controller_status,
        state_hash="controller-state-hash",
        architecture_locked=architecture_locked,
        authoritative=True,
        checkpoint_id=checkpoint_id,
        metadata=metadata,
    )

    acrl = ACRLContinuityView(
        current_gate=acrl_gate,
        current_subtask=acrl_subtask,
        current_task="Implement controller integration",
        checkpoint_id=checkpoint_id,
        architecture_locked=architecture_locked,
        authority_valid=True,
        integrity_valid=integrity_valid,
        resume_safe=resume_safe,
        fingerprint="a" * 64,
        metadata=metadata,
    )

    return ControllerIntegrationRequest(
        controller=controller,
        acrl=acrl,
    )


def test_gate_conflict_fails_closed():
    request = build_request(
        controller_gate="CORE-005",
        acrl_gate="CORE-006",
    )

    report = ControllerIntegrationEngine.integrate(request)

    assert report.decision is IntegrationDecision.FAIL_CLOSED
    assert report.reason is IntegrationReason.GATE_CONFLICT
    assert report.fail_closed is True
    assert report.execution_authorized is False


def test_subtask_conflict_fails_closed():
    request = build_request(
        controller_subtask="CORE-005-T01",
        acrl_subtask="CORE-005-T02",
    )

    report = ControllerIntegrationEngine.integrate(request)

    assert report.decision is IntegrationDecision.FAIL_CLOSED
    assert report.reason is IntegrationReason.SUBTASK_CONFLICT
    assert report.execution_authorized is False


def test_checkpoint_conflict_is_blocked():
    controller = ControllerStateView(
        current_gate="CORE-005",
        current_subtask="CORE-005-T01",
        current_task="Implement controller integration",
        status="CONTROL_CENTER_DRIVEN",
        state_hash="controller-state-hash",
        architecture_locked=True,
        authoritative=True,
        checkpoint_id="CP-T13-001",
    )

    acrl = ACRLContinuityView(
        current_gate="CORE-005",
        current_subtask="CORE-005-T01",
        current_task="Implement controller integration",
        checkpoint_id="CP-T13-002",
        architecture_locked=True,
        authority_valid=True,
        integrity_valid=True,
        resume_safe=True,
        fingerprint="a" * 64,
    )

    request = ControllerIntegrationRequest(
        controller=controller,
        acrl=acrl,
    )

    report = ControllerIntegrationEngine.integrate(request)

    assert report.decision is IntegrationDecision.BLOCKED
    assert report.reason is IntegrationReason.CHECKPOINT_CONFLICT
    assert report.execution_authorized is False


def test_architecture_conflict_fails_closed():
    request = build_request(
        architecture_locked=False,
    )

    controller = request.controller
    acrl = request.acrl

    acrl = ACRLContinuityView(
        current_gate=acrl.current_gate,
        current_subtask=acrl.current_subtask,
        current_task=acrl.current_task,
        checkpoint_id=acrl.checkpoint_id,
        architecture_locked=True,
        authority_valid=acrl.authority_valid,
        integrity_valid=acrl.integrity_valid,
        resume_safe=acrl.resume_safe,
        fingerprint=acrl.fingerprint,
        metadata=acrl.metadata,
    )

    request = ControllerIntegrationRequest(
        controller=controller,
        acrl=acrl,
    )

    report = ControllerIntegrationEngine.integrate(request)

    assert report.decision is IntegrationDecision.FAIL_CLOSED
    assert report.reason is IntegrationReason.ARCHITECTURE_CONFLICT
    assert report.fail_closed is True
    assert report.execution_authorized is False


def test_integrity_conflict_fails_closed():
    request = build_request(integrity_valid=False)

    report = ControllerIntegrationEngine.integrate(request)

    assert report.decision is IntegrationDecision.FAIL_CLOSED
    assert report.reason is IntegrationReason.INTEGRITY_CONFLICT
    assert report.execution_authorized is False


def test_resume_not_safe_is_blocked():
    request = build_request(resume_safe=False)

    report = ControllerIntegrationEngine.integrate(request)

    assert report.decision is IntegrationDecision.BLOCKED
    assert report.reason is IntegrationReason.RESUME_NOT_SAFE
    assert report.resume_authorized is False
    assert report.execution_authorized is False


def test_invalid_metadata_is_rejected():
    request = build_request(
        metadata={
            "nested": {"unsafe": True},
        }
    )

    with pytest.raises(ValueError):
        ControllerIntegrationEngine.integrate(request)


def test_oversized_metadata_is_rejected():
    metadata = {f"field_{index}": index for index in range(65)}

    request = build_request(metadata=metadata)

    with pytest.raises(ValueError):
        ControllerIntegrationEngine.integrate(request)


def test_execution_can_never_be_authorized():
    request = build_request()

    report = ControllerIntegrationEngine.integrate(request)

    assert report.execution_authorized is False


def test_fail_closed_never_authorizes_resume():
    request = build_request(
        controller_gate="",
    )

    report = ControllerIntegrationEngine.integrate(request)

    assert report.fail_closed is True
    assert report.resume_authorized is False
    assert report.execution_authorized is False