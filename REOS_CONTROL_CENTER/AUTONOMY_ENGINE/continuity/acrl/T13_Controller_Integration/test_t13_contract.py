from .controller_integration import (
    ControllerIntegrationEngine,
    ControllerIntegrationRequest,
    IntegrationDecision,
)


def make_request():
    from .controller_integration import (
        ACRLContinuityView,
        ControllerStateView,
    )

    controller = ControllerStateView(
        current_gate="CORE-004",
        current_subtask="CORE-004-T01",
        current_task="Implement project domain",
        status="CONTROL_CENTER_DRIVEN",
        state_hash="a" * 64,
        architecture_locked=True,
        authoritative=True,
        checkpoint_id="CP-001",
        metadata={},
    )

    acrl = ACRLContinuityView(
        current_gate="CORE-004",
        current_subtask="CORE-004-T01",
        current_task="Implement project domain",
        checkpoint_id="CP-001",
        architecture_locked=True,
        authority_valid=True,
        integrity_valid=True,
        resume_safe=True,
        fingerprint="b" * 64,
        metadata={},
    )

    return ControllerIntegrationRequest(
        controller=controller,
        acrl=acrl,
        expected_authority="REOS_CONTROL_CENTER",
    )


def test_report_has_machine_contract():
    report = ControllerIntegrationEngine.integrate(make_request())

    payload = report.to_dict()

    required = {
        "schema_version",
        "authority",
        "decision",
        "reason",
        "request_fingerprint",
        "validated",
        "fail_closed",
        "controller_gate",
        "acrl_gate",
        "controller_subtask",
        "acrl_subtask",
        "resume_authorized",
        "execution_authorized",
        "explanation",
    }

    assert required.issubset(payload.keys())


def test_successful_contract_is_integrated():
    report = ControllerIntegrationEngine.integrate(make_request())

    assert report.decision is IntegrationDecision.INTEGRATED
    assert report.validated is True
    assert report.resume_authorized is True
    assert report.execution_authorized is False


def test_contract_is_deterministic():
    first = ControllerIntegrationEngine.integrate(make_request())
    second = ControllerIntegrationEngine.integrate(make_request())

    assert first.to_dict() == second.to_dict()