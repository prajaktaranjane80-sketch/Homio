from .state_integrity import StateIntegrityEngine
from .fingerprint_metrics import (
    FingerprintMetricsEngine,
)


def _snapshot():
    return StateIntegrityEngine.build(
        {
            "project_identity": {"id": "HOMIO"},
            "architecture": {"version": "1.0"},
            "execution": {"mode": "SAFE"},
            "gate_continuity": {"gate": "T09"},
            "dependency_authority": {
                "authority": "REOS_CONTROL_CENTER"
            },
            "checkpoint": {"id": "cp-001"},
        }
    )


def test_metrics_collect():
    metrics = FingerprintMetricsEngine.collect(
        _snapshot()
    )

    assert metrics.component_count == 6
    assert metrics.component_fingerprint_count == 6


def test_metrics_have_fingerprint_length():
    metrics = FingerprintMetricsEngine.collect(
        _snapshot()
    )

    assert metrics.fingerprint_length == 64


def test_metrics_have_serialized_size():
    metrics = FingerprintMetricsEngine.collect(
        _snapshot()
    )

    assert metrics.serialized_size_bytes > 0


def test_metrics_are_machine_readable():
    metrics = FingerprintMetricsEngine.collect(
        _snapshot()
    )

    data = metrics.to_dict()

    assert isinstance(data, dict)
    assert "component_count" in data
    assert "serialized_size_bytes" in data


def test_metrics_are_deterministic():
    snapshot = _snapshot()

    first = FingerprintMetricsEngine.collect(
        snapshot
    )
    second = FingerprintMetricsEngine.collect(
        snapshot
    )

    assert first == second