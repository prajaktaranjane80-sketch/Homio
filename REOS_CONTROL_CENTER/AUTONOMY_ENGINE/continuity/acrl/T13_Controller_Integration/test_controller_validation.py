import pytest

from .controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationRequest,
    ControllerStateView,
)
from .controller_validation import ControllerValidationEngine


def make_controller(metadata=None):
    return ControllerStateView(
        current_gate="CORE-004",
        current_subtask="CORE-004-T01",
        current_task="Implement project domain.",
        status="CONTROL_CENTER_DRIVEN",
        state_hash="a" * 64,
        architecture_locked=True,
        authoritative=True,
        checkpoint_id="CP-00001",
        metadata={} if metadata is None else metadata,
    )


def make_acrl(metadata=None):
    return ACRLContinuityView(
        current_gate="CORE-004",
        current_subtask="CORE-004-T01",
        current_task="Implement project domain.",
        checkpoint_id="CP-00001",
        architecture_locked=True,
        authority_valid=True,
        integrity_valid=True,
        resume_safe=True,
        fingerprint="b" * 64,
        metadata={} if metadata is None else metadata,
    )


def make_request():
    return ControllerIntegrationRequest(
        controller=make_controller(),
        acrl=make_acrl(),
        expected_authority="REOS_CONTROL_CENTER",
    )


def test_controller_validation_passes():
    assert ControllerValidationEngine.validate_controller(
        make_controller()
    ) is True


def test_acrl_validation_passes():
    assert ControllerValidationEngine.validate_acrl(
        make_acrl()
    ) is True


def test_request_validation_passes():
    assert ControllerValidationEngine.validate_request(
        make_request()
    ) is True


def test_controller_without_authority_is_rejected():
    controller = make_controller()
    controller = type(controller)(
        current_gate=controller.current_gate,
        current_subtask=controller.current_subtask,
        current_task=controller.current_task,
        status=controller.status,
        state_hash=controller.state_hash,
        architecture_locked=controller.architecture_locked,
        authoritative=False,
        checkpoint_id=controller.checkpoint_id,
        metadata=controller.metadata,
    )

    with pytest.raises(ValueError):
        ControllerValidationEngine.validate_controller(controller)


def test_acrl_without_authority_is_rejected():
    acrl = make_acrl()
    acrl = type(acrl)(
        current_gate=acrl.current_gate,
        current_subtask=acrl.current_subtask,
        current_task=acrl.current_task,
        checkpoint_id=acrl.checkpoint_id,
        architecture_locked=acrl.architecture_locked,
        authority_valid=False,
        integrity_valid=acrl.integrity_valid,
        resume_safe=acrl.resume_safe,
        fingerprint=acrl.fingerprint,
        metadata=acrl.metadata,
    )

    with pytest.raises(ValueError):
        ControllerValidationEngine.validate_acrl(acrl)


def test_metadata_field_limit_is_enforced():
    metadata = {f"field_{i}": i for i in range(65)}

    with pytest.raises(ValueError):
        ControllerValidationEngine.validate_metadata(metadata)


def test_metadata_key_limit_is_enforced():
    metadata = {"x" * 129: "value"}

    with pytest.raises(ValueError):
        ControllerValidationEngine.validate_metadata(metadata)


def test_metadata_string_limit_is_enforced():
    metadata = {"value": "x" * 4097}

    with pytest.raises(ValueError):
        ControllerValidationEngine.validate_metadata(metadata)


def test_nested_metadata_is_rejected():
    metadata = {"nested": {"unsafe": True}}

    with pytest.raises(ValueError):
        ControllerValidationEngine.validate_metadata(metadata)