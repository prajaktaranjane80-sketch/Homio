from .state_integrity import StateIntegrityEngine
from .fingerprint_identity import FingerprintIdentityEngine
from .fingerprint_provenance import (
    FingerprintProvenanceEngine,
)
from .fingerprint_validation import (
    FingerprintValidationEngine,
)
from .fingerprint_compatibility import (
    FingerprintCompatibilityEngine,
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


def test_t09_contract_pipeline():
    snapshot = _snapshot()

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    validation = FingerprintValidationEngine.validate(
        snapshot,
        identity,
        provenance,
    )

    compatibility = (
        FingerprintCompatibilityEngine.validate_all(
            snapshot.schema_version,
            identity.identity_version,
            provenance.provenance_version,
        )
    )

    registry = FingerprintRegistryEngine.register(
        FingerprintRegistryEngine.empty(),
        snapshot,
        identity,
        provenance,
    )

    metrics = FingerprintMetricsEngine.collect(
        snapshot
    )

    assert validation.valid is True
    assert len(compatibility) == 3
    assert registry.contains(
        snapshot.overall_fingerprint
    )
    assert metrics.component_count == 6


def test_t09_contract_preserves_authority():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )
    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    assert snapshot.authority == (
        "REOS_CONTROL_CENTER"
    )
    assert identity.authority == (
        "REOS_CONTROL_CENTER"
    )
    assert provenance.source_authority == (
        "REOS_CONTROL_CENTER"
    )