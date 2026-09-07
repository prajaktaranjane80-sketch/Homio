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
        assert ControllerIntegrationAuthorityError is not None
        assert ControllerIntegrationConflictError is not None
        assert ControllerIntegrationEngine is not None
        assert ControllerIntegrationRequest is not None
        assert ControllerIntegrationValidationError is not None
        assert ControllerStateView is not None
        assert IntegrationDecision is not None
        assert IntegrationReason is not None

    def test_public_api_functions_available(self) -> None:
        from AUTONOMY_ENGINE.continuity.acrl.controller_integration import (
            controller_resume_authorized,
            integrate_controller,
        )

        assert callable(controller_resume_authorized)
        assert callable(integrate_controller)


class TestSerializationContract:
    """Test serialization method contracts."""

    def test_request_to_dict_serializes(self) -> None:
        request = ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(),
        )

        data = request.to_dict()

        assert isinstance(data, dict)
        assert "controller" in data
        assert "acrl" in data
        assert "expected_authority" in data

    def test_report_to_dict_serializes(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(),
            )
        )

        data = report.to_dict()

        assert isinstance(data, dict)
        assert "schema_version" in data
        assert "authority" in data
        assert "decision" in data
        assert "reason" in data

    def test_enum_values_serialize_as_strings(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(),
            )
        )

        data = report.to_dict()

        assert isinstance(data["decision"], str)
        assert isinstance(data["reason"], str)


class TestAuthorityContract:
    """Test authority enforcement contract."""

    def test_authority_always_reos_control_center(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(),
            )
        )

        assert report.authority == "REOS_CONTROL_CENTER"

    def test_schema_version_stable(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(),
            )
        )

        assert report.schema_version == "1.0"


class TestIdempotencyContract:
    """Test idempotency guarantees."""

    def test_identical_requests_produce_identical_reports(self) -> None:
        request = ControllerIntegrationRequest(
            controller=make_controller(),
            acrl=make_acrl(),
        )

        report1 = integrate_controller(request)
        report2 = integrate_controller(request)

        assert report1.to_dict() == report2.to_dict()
