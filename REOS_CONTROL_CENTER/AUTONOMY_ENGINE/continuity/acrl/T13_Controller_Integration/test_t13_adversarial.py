"""ACRL T13 — Controller Integration Adversarial Tests."""

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


class TestAdversarialInvalidTypes:
    """Test rejection of invalid request types."""

    def test_invalid_request_object_rejected(self) -> None:
        with pytest.raises(
            ControllerIntegrationValidationError
        ):
            ControllerIntegrationEngine.integrate(
                object()  # type: ignore
            )


class TestAdversarialAuthority:
    """Test authority enforcement."""

    def test_controller_authority_false_rejected(self) -> None:
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

    def test_acrl_authority_false_rejected(self) -> None:
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


class TestAdversarialConflicts:
    """Test conflict detection."""

    def test_empty_gate_fails_closed(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(gate=""),
                acrl=make_acrl(),
            )
        )

        assert (
            report.decision
            == IntegrationDecision.FAIL_CLOSED
        )
        assert (
            report.reason
            == IntegrationReason.CONTROLLER_UNAVAILABLE
        )

    def test_integrity_false_fails_closed(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(integrity_valid=False),
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


class TestAdversarialExecution:
    """Test execution authorization guarantees."""

    def test_execution_never_authorized_on_success(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(),
            )
        )

        assert report.execution_authorized is False
