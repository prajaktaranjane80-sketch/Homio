from .state_integrity import StateIntegrityEngine
from .fingerprint_identity import FingerprintIdentityEngine
from .fingerprint_provenance import (
    FingerprintProvenanceEngine,
)
from .fingerprint_validation import (
    FingerprintValidationEngine,
)
from .fingerprint_registry import (
    FingerprintRegistryEngine,
)
from .fingerprint_metrics import (
    FingerprintMetricsEngine,
)


def _snapshot():
    return StateIntegrityEngine.build(
        {
            "project_identity": {
                "project": "HOMIO"
            },
            "architecture": {
                "locked": True
            },
            "execution": {
                "mode": "SAFE_AUTONOMOUS_RESUME"
            },
            "gate_continuity": {
                "gate": "T09"
            },
            "dependency_authority": {
                "authority": "REOS_CONTROL_CENTER"
            },
            "checkpoint": {
                "id": "checkpoint-001"
            },
        }
    )


def test_end_to_end_t09_pipeline():
    snapshot = _snapshot()

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    assert FingerprintIdentityEngine.validate(
        identity
    )

    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    assert FingerprintProvenanceEngine.validate(
        provenance
    )

    validation = FingerprintValidationEngine.validate_or_raise(
        snapshot,
        identity,
        provenance,
    )

    registry = FingerprintRegistryEngine.empty()

    registry = FingerprintRegistryEngine.register(
        registry,
        snapshot,
        identity,
        provenance,
    )

    metrics = FingerprintMetricsEngine.collect(
        snapshot
    )

    assert validation.valid is True
    assert registry.contains(
        snapshot.overall_fingerprint
    )
    assert metrics.verified is False


def test_repeated_pipeline_is_deterministic():
    snapshot = _snapshot()

    first_identity = (
        FingerprintIdentityEngine.build(
            snapshot
        )
    )

    second_identity = (
        FingerprintIdentityEngine.build(
            snapshot
        )
    )

    first_provenance = (
        FingerprintProvenanceEngine.build(
            snapshot,
            first_identity,
        )
    )

    second_provenance = (
        FingerprintProvenanceEngine.build(
            snapshot,
            second_identity,
        )
    )

    assert first_identity == second_identity
    assert first_provenance == second_provenance


def test_source_snapshot_is_not_mutated():
    snapshot = _snapshot()
    before = snapshot

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    FingerprintMetricsEngine.collect(
        snapshot
    )

    assert snapshot == before