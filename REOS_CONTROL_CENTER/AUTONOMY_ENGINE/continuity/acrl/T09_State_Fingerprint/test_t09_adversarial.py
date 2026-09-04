import pytest

from .state_integrity import StateIntegrityEngine
from .fingerprint_identity import FingerprintIdentityEngine
from .fingerprint_provenance import (
    FingerprintProvenanceEngine,
)
from .fingerprint_validation import (
    FingerprintValidationEngine,
    FingerprintValidationIntegrityError,
)
from .fingerprint_compatibility import (
    FingerprintCompatibilityEngine,
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


def test_authority_spoof_is_rejected():
    snapshot = _snapshot()

    tampered = type(snapshot)(
        schema_version=snapshot.schema_version,
        authority="ATTACKER",
        components=snapshot.components,
        component_fingerprints=snapshot.component_fingerprints,
        overall_fingerprint=snapshot.overall_fingerprint,
        algorithm=snapshot.algorithm,
    )

    result = FingerprintValidationEngine.validate(
        tampered
    )

    assert result.valid is False
    assert result.authority_valid is False


def test_unknown_schema_fails_closed():
    result = FingerprintCompatibilityEngine.check_schema(
        "T09-UNKNOWN"
    )

    assert result.accepted is False


def test_unknown_identity_fails_closed():
    result = FingerprintCompatibilityEngine.check_identity(
        "T09-IDENTITY-UNKNOWN"
    )

    assert result.accepted is False


def test_tampered_identity_is_rejected():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    tampered = type(identity)(
        identity_version=identity.identity_version,
        schema_version=identity.schema_version,
        authority=identity.authority,
        algorithm=identity.algorithm,
        overall_fingerprint=identity.overall_fingerprint,
        identity_fingerprint="0" * 64,
    )

    with pytest.raises(Exception):
        FingerprintIdentityEngine.validate(
            tampered
        )


def test_tampered_provenance_is_rejected():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )
    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    tampered = type(provenance)(
        provenance_version=provenance.provenance_version,
        source_schema_version=provenance.source_schema_version,
        source_authority=provenance.source_authority,
        source_algorithm=provenance.source_algorithm,
        source_fingerprint="0" * 64,
        identity_fingerprint=provenance.identity_fingerprint,
        provenance_fingerprint=provenance.provenance_fingerprint,
    )

    with pytest.raises(Exception):
        FingerprintProvenanceEngine.validate(
            tampered
        )


def test_fingerprint_package_fails_closed_on_mismatch():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )
    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )

    tampered = type(identity)(
        identity_version=identity.identity_version,
        schema_version=identity.schema_version,
        authority=identity.authority,
        algorithm=identity.algorithm,
        overall_fingerprint="1" * 64,
        identity_fingerprint=identity.identity_fingerprint,
    )

    result = FingerprintValidationEngine.validate(
        snapshot,
        tampered,
        provenance,
    )

    assert result.valid is False