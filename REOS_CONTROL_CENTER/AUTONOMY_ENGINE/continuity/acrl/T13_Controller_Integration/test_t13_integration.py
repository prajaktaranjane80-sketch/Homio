"""ACRL T13 — Controller Integration integration tests."""

from .controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationEngine,
    ControllerIntegrationRequest,
    ControllerStateView,
    IntegrationDecision,
)


def build_request():
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
        checkpoint_id="CP-T13-001",
        architecture_locked=True,
        authority_valid=True,
        integrity_valid=True,
        resume_safe=True,
        fingerprint="a" * 64,
    )

    return ControllerIntegrationRequest(
        controller=controller,
        acrl=acrl,
    )


def test_successful_controller_integration():
    request = build_request()

    report = ControllerIntegrationEngine.integrate(request)

    assert report.decision is IntegrationDecision.INTEGRATED
    assert report.resume_authorized is True
    assert report.execution_authorized is False
    assert report.fail_closed is False


def test_can_resume_matches_integration():
    request = build_request()

    report = ControllerIntegrationEngine.integrate(request)

    assert ControllerIntegrationEngine.can_resume(report) is True
    assert report.resume_authorized is True


def test_integration_does_not_mutate_inputs():
    request = build_request()

    before_controller = request.controller.to_dict()
    before_acrl = request.acrl.to_dict()

    ControllerIntegrationEngine.integrate(request)

    assert request.controller.to_dict() == before_controller
    assert request.acrl.to_dict() == before_acrl


def test_success_is_deterministic():
    request = build_request()

    first = ControllerIntegrationEngine.integrate(request)
    second = ControllerIntegrationEngine.integrate(request)

    assert first.to_dict() == second.to_dict()
    assert first.request_fingerprint == second.request_fingerprint


def test_success_never_authorizes_execution():
    request = build_request()

    report = ControllerIntegrationEngine.integrate(request)

    assert report.execution_authorized is False


def test_resume_requires_integrated_report():
    request = build_request()

    report = ControllerIntegrationEngine.integrate(request)

    assert ControllerIntegrationEngine.can_resume(report) is True