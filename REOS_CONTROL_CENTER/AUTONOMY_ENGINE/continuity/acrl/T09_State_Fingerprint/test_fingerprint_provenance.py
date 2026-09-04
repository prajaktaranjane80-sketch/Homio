from .state_integrity import StateIntegrityEngine
from .fingerprint_identity import FingerprintIdentityEngine
from .fingerprint_provenance import (
    FingerprintProvenanceEngine,
    FingerprintProvenanceValidationError,
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


def test_provenance_builds():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    assert provenance.source_fingerprint == (
        snapshot.overall_fingerprint
    )


def test_provenance_validates():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    assert FingerprintProvenanceEngine.validate(
        provenance
    )


def test_provenance_is_deterministic():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    first = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )
    second = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    assert first == second


def test_wrong_identity_is_rejected():
    snapshot = _snapshot()

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    wrong = type(identity)(
        identity_version=identity.identity_version,
        schema_version=identity.schema_version,
        authority=identity.authority,
        algorithm=identity.algorithm,
        overall_fingerprint=identity.overall_fingerprint,
        identity_fingerprint="1" * 64,
    )

    try:
        FingerprintProvenanceEngine.build(
            snapshot,
            wrong,
        )
        assert False
    except FingerprintProvenanceValidationError:
        assert True