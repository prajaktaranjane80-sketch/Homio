from .controller_identity import ControllerIdentityEngine
from .controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationRequest,
    ControllerStateView,
)


def make_request():
    controller = ControllerStateView(
        current_gate="CORE-004",
        current_subtask="CORE-004-T01",
        current_task="Implement project domain.",
        status="CONTROL_CENTER_DRIVEN",
        state_hash="a" * 64,
        architecture_locked=True,
        authoritative=True,
        checkpoint_id="CP-00001",
        metadata={},
    )

    acrl = ACRLContinuityView(
        current_gate="CORE-004",
        current_subtask="CORE-004-T01",
        current_task="Implement project domain.",
        checkpoint_id="CP-00001",
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


def test_request_fingerprint_is_deterministic():
    request = make_request()

    first = ControllerIdentityEngine.fingerprint_request(request)
    second = ControllerIdentityEngine.fingerprint_request(request)

    assert first == second
    assert len(first) == 64


def test_identity_is_deterministic():
    request = make_request()

    first = ControllerIdentityEngine.build(request)
    second = ControllerIdentityEngine.build(request)

    assert first.fingerprint == second.fingerprint
    assert first.request_fingerprint == second.request_fingerprint


def test_identity_is_valid():
    identity = ControllerIdentityEngine.build(make_request())

    assert ControllerIdentityEngine.validate(identity) is True


def test_identity_serialization():
    identity = ControllerIdentityEngine.build(make_request())
    data = identity.to_dict()

    assert data["identity_version"] == "T13-IDENTITY-1.0"
    assert data["schema_version"] == "1.0"
    assert data["authority"] == "REOS_CONTROL_CENTER"
    assert len(data["fingerprint"]) == 64


def test_tampered_identity_is_rejected():
    identity = ControllerIdentityEngine.build(make_request())

    tampered = type(identity)(
        identity_version=identity.identity_version,
        schema_version=identity.schema_version,
        authority=identity.authority,
        request_fingerprint=identity.request_fingerprint,
        fingerprint="0" * 64,
        algorithm=identity.algorithm,
    )

    try:
        ControllerIdentityEngine.validate(tampered)
    except ValueError:
        return

    raise AssertionError("Tampered identity was accepted.")
