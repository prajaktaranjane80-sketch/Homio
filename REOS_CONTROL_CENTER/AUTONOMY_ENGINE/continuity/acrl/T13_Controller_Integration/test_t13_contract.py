"""ACRL T13 — Controller Integration Contract Tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationEngine,
    ControllerIntegrationRequest,
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


class TestPublicAPIContract:
    """Test public API availability and stability."""

    def test_public_api_classes_available(self) -> None:
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
        )

        assert ACRLContinuityView is not None

    def test_execute_authorization_never_true(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(),
            )
        )
        assert report.execution_authorized is False
