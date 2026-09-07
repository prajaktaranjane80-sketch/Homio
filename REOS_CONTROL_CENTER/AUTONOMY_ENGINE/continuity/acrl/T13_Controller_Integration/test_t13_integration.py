"""ACRL T13 — Controller Integration Pipeline Tests.

Integration test verifying the complete T09→T10→T11→T12→T13 pipeline.
T13 must consume upstream evidence without taking authority from REOS_CONTROL_CENTER.
"""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationEngine,
    ControllerIntegrationRequest,
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


class TestT13PipelineHealthy:
    """Test healthy T09→T13 pipeline integration."""

    def test_t13_accepts_valid_evidence(self) -> None:
        """T13 receives valid evidence and authorizes resumption."""
        controller = make_controller()
        acrl = make_acrl()

        request = ControllerIntegrationRequest(
            controller=controller,
            acrl=acrl,
        )

        report = integrate_controller(request)

        assert (
            report.decision
            == IntegrationDecision.INTEGRATED
        )
        assert report.resume_authorized is True
        assert report.execution_authorized is False

    def test_t13_preserves_reos_authority(self) -> None:
        """T13 does not take authority."""
        request = ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(),
        )

        report = integrate_controller(request)

        assert report.authority == "REOS_CONTROL_CENTER"

    def test_t13_no_mutations(self) -> None:
        """T13 does not mutate upstream evidence."""
        controller = make_controller()
        acrl = make_acrl()

        controller_before = controller.to_dict()
        acrl_before = acrl.to_dict()

        request = ControllerIntegrationRequest(
            controller=controller,
            acrl=acrl,
        )

        integrate_controller(request)

        assert controller.to_dict() == controller_before
        assert acrl.to_dict() == acrl_before


class TestT13PipelineIdempotency:
    """Test idempotency for repeated pipeline invocations."""

    def test_t13_idempotent(self) -> None:
        """Multiple calls with same evidence produce identical reports."""
        request = ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(),
        )

        report1 = integrate_controller(request)
        report2 = integrate_controller(request)
        report3 = integrate_controller(request)

        assert report1.to_dict() == report2.to_dict()
        assert report2.to_dict() == report3.to_dict()
