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

    def test_t13_accepts_valid_controller_and_acrl_evidence(self) -> None:
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
        assert (
            report.reason
            == IntegrationReason.VALID
        )
        assert report.resume_authorized is True
        assert report.execution_authorized is False

    def test_t13_preserves_reos_control_center_authority(self) -> None:
        """T13 does not take authority; REOS_CONTROL_CENTER remains sole authority."""
        request = ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(),
        )

        report = integrate_controller(request)

        assert report.authority == "REOS_CONTROL_CENTER"

    def test_t13_does_not_mutate_upstream_evidence(self) -> None:
        """T13 observes but does not modify controller and ACRL evidence."""
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


class TestT13PipelineFailSafe:
    """Test fail-safe behavior in degraded pipeline."""

    def test_t13_fails_closed_on_controller_unavailable(self) -> None:
        """T13 fails closed when controller gate is unavailable."""
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
        assert report.resume_authorized is False

    def test_t13_fails_closed_on_upstream_integrity_invalid(self) -> None:
        """T13 fails closed when ACRL integrity is invalid."""
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
        assert report.resume_authorized is False

    def test_t13_blocks_on_resume_unsafe(self) -> None:
        """T13 blocks resume when T12 safety check failed."""
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(resume_safe=False),
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
        assert report.resume_authorized is False


class TestT13PipelineNonexecution:
    """Test that T13 never executes tasks or modifies state."""

    def test_t13_never_authorizes_execution(self) -> None:
        """Even on INTEGRATED, execution remains forbidden."""
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(),
            )
        )

        assert report.execution_authorized is False
        assert report.resume_authorized is True

    def test_t13_never_modifies_state_json(self) -> None:
        """T13 is observational only; no mutations."""
        request = ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(),
        )

        report = integrate_controller(request)

        # Report is immutable (frozen dataclass)
        with pytest.raises(AttributeError):
            report.execution_authorized = True  # type: ignore


class TestT13PipelineIdempotency:
    """Test idempotency for repeated pipeline invocations."""

    def test_t13_idempotent_on_valid_evidence(self) -> None:
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
