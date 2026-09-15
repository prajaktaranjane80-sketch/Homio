"""T13 — Control Center context adapter acceptance tests."""

from __future__ import annotations

import copy

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T13_Controller_Integration.controller_context_adapter import (
    ControllerContextAdapter,
    ControllerContextAuthorityError,
    ControllerContextStateError,
)
from AUTONOMY_ENGINE.continuity.acrl.T13_Controller_Integration.controller_integration import (
    ACRLContinuityView,
    IntegrationDecision,
)


def make_state() -> dict:
    return {
        "meta": {
            "version": "3.4",
            "schema_version": 3,
            "control_center_version": "7.0",
        },
        "constitution": {
            "single_source_of_truth": True,
            "autonomous_plan_is_authority": True,
            "next_step_must_come_from_control_center": True,
            "gate_subtasks_are_authoritative": True,
            "assistant_executes_current_subtask_only": True,
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
        "architecture": {
            "locked": True,
        },
        "execution": {
            "current_gate": "CORE-004",
            "current_task": "Implement inventory domain.",
            "current_subtask": "CORE-004-T02",
            "status": "CONTROL_CENTER_DRIVEN",
            "checkpoint_id": "CP-00001",
        },
        "gate_plans": {
            "CORE-004": {
                "current_subtask": "CORE-004-T02",
            }
        },
        "integrity": {
            "sha256": "a" * 64,
        },
    }


def make_acrl() -> ACRLContinuityView:
    return ACRLContinuityView(
        current_gate="CORE-004",
        current_subtask="CORE-004-T02",
        current_task="Implement inventory domain.",
        checkpoint_id="CP-00001",
        architecture_locked=True,
        authority_valid=True,
        integrity_valid=True,
        resume_safe=True,
        fingerprint="b" * 64,
    )


def test_maps_canonical_control_center_state() -> None:
    view = ControllerContextAdapter.controller_view_from_state(
        make_state()
    )

    assert view.current_gate == "CORE-004"
    assert view.current_task == "Implement inventory domain."
    assert view.current_subtask == "CORE-004-T02"
    assert view.status == "CONTROL_CENTER_DRIVEN"
    assert view.checkpoint_id == "CP-00001"
    assert view.architecture_locked is True
    assert view.authoritative is True
    assert view.state_hash == "a" * 64


def test_subtask_can_be_reconstructed_from_gate_plan() -> None:
    state = make_state()
    state["execution"].pop("current_subtask")

    view = ControllerContextAdapter.controller_view_from_state(
        state
    )

    assert view.current_subtask == "CORE-004-T02"


def test_authority_contract_is_required() -> None:
    state = make_state()
    state["constitution"]["next_step_must_come_from_control_center"] = False

    with pytest.raises(ControllerContextAuthorityError):
        ControllerContextAdapter.controller_view_from_state(
            state
        )


def test_integrity_hash_is_required() -> None:
    state = make_state()
    del state["integrity"]["sha256"]

    with pytest.raises(ControllerContextAuthorityError):
        ControllerContextAdapter.controller_view_from_state(
            state
        )


def test_current_gate_is_required() -> None:
    state = make_state()
    del state["execution"]["current_gate"]

    with pytest.raises(ControllerContextStateError):
        ControllerContextAdapter.controller_view_from_state(
            state
        )


def test_current_task_is_required() -> None:
    state = make_state()
    del state["execution"]["current_task"]

    with pytest.raises(ControllerContextStateError):
        ControllerContextAdapter.controller_view_from_state(
            state
        )


def test_controller_status_is_required() -> None:
    state = make_state()
    del state["execution"]["status"]

    with pytest.raises(ControllerContextStateError):
        ControllerContextAdapter.controller_view_from_state(
            state
        )


def test_adapter_does_not_mutate_control_center_state() -> None:
    state = make_state()
    before = copy.deepcopy(state)

    ControllerContextAdapter.controller_view_from_state(
        state
    )

    assert state == before


def test_adapter_builds_existing_t13_request_boundary() -> None:
    request = ControllerContextAdapter.build_request(
        make_state(),
        make_acrl(),
    )

    assert request.expected_authority == "REOS_CONTROL_CENTER"
    assert request.controller.current_task == (
        "Implement inventory domain."
    )
    assert request.controller.current_subtask == "CORE-004-T02"


def test_adapter_reaches_existing_t13_engine() -> None:
    report = ControllerContextAdapter.integrate(
        make_state(),
        make_acrl(),
    )

    assert report.decision == IntegrationDecision.INTEGRATED
    assert report.resume_authorized is True
    assert report.execution_authorized is False


def test_execution_authority_remains_control_center_only() -> None:
    report = ControllerContextAdapter.integrate(
        make_state(),
        make_acrl(),
    )

    assert report.authority == "REOS_CONTROL_CENTER"
    assert report.execution_authorized is False
