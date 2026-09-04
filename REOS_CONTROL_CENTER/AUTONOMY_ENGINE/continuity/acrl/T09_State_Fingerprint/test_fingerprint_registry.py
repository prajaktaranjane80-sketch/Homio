from .state_integrity import StateIntegrityEngine
from .fingerprint_identity import FingerprintIdentityEngine
from .fingerprint_provenance import (
    FingerprintProvenanceEngine,
)
from .fingerprint_registry import (
    FingerprintRegistryEngine,
    FingerprintRegistryConflictError,
)


def _package():
    snapshot = StateIntegrityEngine.build(
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

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    return snapshot, identity, provenance


def test_empty_registry():
    registry = FingerprintRegistryEngine.empty()

    assert registry.entries == ()


def test_registers_valid_fingerprint():
    snapshot, identity, provenance = _package()
    registry = FingerprintRegistryEngine.empty()

    result = FingerprintRegistryEngine.register(
        registry,
        snapshot,
        identity,
        provenance,
    )

    assert result.contains(
        snapshot.overall_fingerprint
    )


def test_registration_is_replay_safe():
    snapshot, identity, provenance = _package()
    registry = FingerprintRegistryEngine.empty()

    first = FingerprintRegistryEngine.register(
        registry,
        snapshot,
        identity,
        provenance,
    )

    second = FingerprintRegistryEngine.register(
        first,
        snapshot,
        identity,
        provenance,
    )

    assert second == first


def test_registry_lookup():
    snapshot, identity, provenance = _package()
    registry = FingerprintRegistryEngine.register(
        FingerprintRegistryEngine.empty(),
        snapshot,
        identity,
        provenance,
    )

    entry = registry.get(
        snapshot.overall_fingerprint
    )

    assert entry is not None
    assert entry.authority == (
        "REOS_CONTROL_CENTER"
    )


def test_registry_is_immutable():
    snapshot, identity, provenance = _package()
    registry = FingerprintRegistryEngine.register(
        FingerprintRegistryEngine.empty(),
        snapshot,
        identity,
        provenance,
    )

    assert len(registry.entries) == 1