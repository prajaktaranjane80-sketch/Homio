"""ACRL T13 — Controller Integration Metrics Regression Tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationEngine,
    ControllerIntegrationReport,
    ControllerIntegrationRequest,
    ControllerStateView,
    IntegrationDecision,
    IntegrationReason,
    integrate_controller,
)

from .controller_metrics import (
    ControllerMetrics,
    ControllerMetricsEngine,
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


def make_request(**kwargs) -> ControllerIntegrationRequest:
    controller_kwargs = {}
    acrl_kwargs = {}

    controller_fields = {
        "gate",
        "subtask",
        "task",
        "status",
        "architecture_locked",
        "authoritative",
        "checkpoint_id",
    }

    acrl_fields = {
        "gate",
        "subtask",
        "task",
        "checkpoint_id",
        "architecture_locked",
        "authority_valid",
        "integrity_valid",
        "resume_safe",
    }

    controller_values = {
        key: value
        for key, value in kwargs.items()
        if key in controller_fields
    }

    acrl_values = {
        key: value
        for key, value in kwargs.items()
        if key in acrl_fields
    }

    controller_kwargs = controller_values
    acrl_kwargs = acrl_values

    return ControllerIntegrationRequest(
        controller=make_controller(
            **controller_kwargs
        ),
        acrl=make_acrl(
            **acrl_kwargs
        ),
    )


class TestControllerMetricsBasic:
    """Basic metrics aggregation tests."""

    def test_metrics_total_integrations_increments(self) -> None:
        report1 = integrate_controller(make_request())
        report2 = integrate_controller(make_request())

        metrics = ControllerMetricsEngine.summarize(
            [report1, report2]
        )

        assert metrics.total_integrations == 2

    def test_metrics_integrated_count_works(self) -> None:
        report = integrate_controller(make_request())
        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.integrated == 1
        assert metrics.blocked == 0
        assert metrics.fail_closed == 0

    def test_metrics_blocked_count_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(
                    status="PAUSED"
                ),
                acrl=make_acrl(),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.blocked == 1
        assert metrics.integrated == 0
        assert metrics.fail_closed == 0

    def test_metrics_fail_closed_count_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(
                    gate="CORE-005"
                ),
                acrl=make_acrl(
                    gate="CORE-004"
                ),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.fail_closed == 1
        assert metrics.integrated == 0
        assert metrics.blocked == 0


class TestControllerMetricsConflicts:
    """Metrics conflict counter tests."""

    def test_metrics_gate_conflict_counter_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(
                    gate="CORE-005"
                ),
                acrl=make_acrl(
                    gate="CORE-004"
                ),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.gate_conflicts == 1

    def test_metrics_subtask_conflict_counter_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(
                    subtask="CORE-004-T02"
                ),
                acrl=make_acrl(
                    subtask="CORE-004-T01"
                ),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.subtask_conflicts == 1

    def test_metrics_checkpoint_conflict_counter_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(
                    checkpoint_id="CP-00002"
                ),
                acrl=make_acrl(
                    checkpoint_id="CP-00001"
                ),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.checkpoint_conflicts == 1

    def test_metrics_integrity_conflict_counter_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(
                    integrity_valid=False
                ),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.integrity_conflicts == 1

    def test_metrics_architecture_conflict_counter_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(
                    architecture_locked=True
                ),
                acrl=make_acrl(
                    architecture_locked=False
                ),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.architecture_conflicts == 1

    def test_metrics_resume_not_safe_counter_works(self) -> None:
        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(
                    resume_safe=False
                ),
            )
        )

        metrics = ControllerMetricsEngine.summarize([report])

        assert metrics.resume_not_safe == 1


class TestControllerMetricsSafety:
    """Metrics observational safety tests."""

    def test_metrics_do_not_mutate_controller(self) -> None:
        controller = make_controller()
        original = controller.to_dict()

        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=controller,
                acrl=make_acrl(),
            )
        )

        ControllerMetricsEngine.summarize([report])

        assert controller.to_dict() == original

    def test_metrics_do_not_mutate_acrl(self) -> None:
        acrl = make_acrl()
        original = acrl.to_dict()

        report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=acrl,
            )
        )

        ControllerMetricsEngine.summarize([report])

        assert acrl.to_dict() == original

    def test_metrics_do_not_mutate_request(self) -> None:
        request = make_request()
        original = request.to_dict()

        report = integrate_controller(request)
        ControllerMetricsEngine.summarize([report])

        assert request.to_dict() == original

    def test_metrics_do_not_mutate_report(self) -> None:
        report = integrate_controller(make_request())
        original = report.to_dict()

        ControllerMetricsEngine.summarize([report])

        assert report.to_dict() == original


class TestControllerMetricsNormalization:
    """Metrics enum/string normalization tests."""

    def test_metrics_normalize_enum_values_safely(self) -> None:
        report = integrate_controller(make_request())
        metrics = ControllerMetricsEngine.summarize([report])

        assert isinstance(metrics.integrated, int)
        assert metrics.integrated >= 0

    def test_metrics_handle_string_reason_values(self) -> None:
        # Metrics engine extracts reason.value from enum
        report = integrate_controller(make_request())

        assert hasattr(report.reason, "value")
        assert isinstance(report.reason.value, str)

        metrics = ControllerMetricsEngine.summarize([report])

        # No exception should occur
        assert metrics.total_integrations == 1

    def test_metrics_handle_string_decision_values(self) -> None:
        # Metrics engine extracts decision.value from enum
        report = integrate_controller(make_request())

        assert hasattr(report.decision, "value")
        assert isinstance(report.decision.value, str)

        metrics = ControllerMetricsEngine.summarize([report])

        # No exception should occur
        assert metrics.total_integrations == 1


class TestControllerMetricsObservational:
    """Metrics observational-only behavior tests."""

    def test_metrics_are_observational_only(self) -> None:
        reports = [
            integrate_controller(make_request()),
            integrate_controller(
                ControllerIntegrationRequest(
                    controller=make_controller(
                        gate="CORE-005"
                    ),
                    acrl=make_acrl(
                        gate="CORE-004"
                    ),
                )
            ),
        ]

        metrics = ControllerMetricsEngine.summarize(reports)

        # Metrics should not modify reports
        for report in reports:
            assert report.execution_authorized is False

    def test_metrics_serialization(self) -> None:
        report = integrate_controller(make_request())
        metrics = ControllerMetricsEngine.summarize([report])

        data = metrics.to_dict()

        assert "metric_version" in data
        assert data["metric_version"] == "T13-METRICS-1.0"
        assert data["total_integrations"] == 1

    def test_metrics_from_report_helper(self) -> None:
        report = integrate_controller(make_request())
        data = ControllerMetricsEngine.from_report(report)

        assert isinstance(data, dict)
        assert data["total_integrations"] == 1
        assert data["integrated"] == 1


class TestControllerMetricsMultiple:
    """Metrics aggregation across multiple reports."""

    def test_metrics_aggregate_mixed_decisions(self) -> None:
        integrated_report = integrate_controller(make_request())
        
        blocked_report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(status="PAUSED"),
                acrl=make_acrl(),
            )
        )
        
        fail_closed_report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(gate="CORE-005"),
                acrl=make_acrl(gate="CORE-004"),
            )
        )

        metrics = ControllerMetricsEngine.summarize(
            [integrated_report, blocked_report, fail_closed_report]
        )

        assert metrics.total_integrations == 3
        assert metrics.integrated == 1
        assert metrics.blocked == 1
        assert metrics.fail_closed == 1

    def test_metrics_aggregate_mixed_conflicts(self) -> None:
        gate_report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(gate="CORE-005"),
                acrl=make_acrl(gate="CORE-004"),
            )
        )
        
        subtask_report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(subtask="CORE-004-T02"),
                acrl=make_acrl(subtask="CORE-004-T01"),
            )
        )
        
        integrity_report = integrate_controller(
            ControllerIntegrationRequest(
                controller=make_controller(),
                acrl=make_acrl(integrity_valid=False),
            )
        )

        metrics = ControllerMetricsEngine.summarize(
            [gate_report, subtask_report, integrity_report]
        )

        assert metrics.gate_conflicts == 1
        assert metrics.subtask_conflicts == 1
        assert metrics.integrity_conflicts == 1

    def test_metrics_empty_list_returns_zeros(self) -> None:
        metrics = ControllerMetricsEngine.summarize([])

        assert metrics.total_integrations == 0
        assert metrics.integrated == 0
        assert metrics.blocked == 0
        assert metrics.fail_closed == 0
        assert metrics.gate_conflicts == 0
