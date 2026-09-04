"""Tests for T11 recovery metrics."""

from __future__ import annotations

from .recovery_guard import (
    RecoveryRequest,
    evaluate_recovery,
)
from .recovery_metrics import (
    RecoveryMetrics,
    RecoveryMetricsEngine,
)


def make_request() -> RecoveryRequest:
    return RecoveryRequest(
        failure_type="timeout",
        component="execution",
        recoverable=True,
        authoritative=True,
        integrity_verified=True,
    )


def test_metrics_collect() -> None:
    report = evaluate_recovery(make_request())

    metrics = RecoveryMetricsEngine.collect(
        report
    )

    assert isinstance(
        metrics,
        RecoveryMetrics,
    )


def test_metrics_detect_recovery() -> None:
    report = evaluate_recovery(make_request())
    metrics = RecoveryMetricsEngine.collect(report)

    assert metrics.decision == "RECOVER"
    assert metrics.fail_closed is False


def test_metrics_fingerprint_length() -> None:
    report = evaluate_recovery(make_request())
    metrics = RecoveryMetricsEngine.collect(report)

    assert metrics.fingerprint_length == 64


def test_metrics_are_machine_readable() -> None:
    report = evaluate_recovery(make_request())
    metrics = RecoveryMetricsEngine.collect(report)

    data = metrics.to_dict()

    assert data["decision"] == "RECOVER"


def test_metrics_are_deterministic() -> None:
    report = evaluate_recovery(make_request())

    first = RecoveryMetricsEngine.collect(
        report
    ).to_dict()

    second = RecoveryMetricsEngine.collect(
        report
    ).to_dict()

    assert first == second