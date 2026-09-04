from .state_integrity import StateIntegrityEngine
from .fingerprint_identity import FingerprintIdentityEngine
from .fingerprint_provenance import (
    FingerprintProvenanceEngine,
)
from .fingerprint_validation import (
    FingerprintValidationEngine,
    FingerprintValidationIntegrityError,
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


def _package():
    snapshot = _snapshot()
    identity = FingerprintIdentityEngine.build(
        snapshot
    )
    provenance = FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )
    return snapshot, identity, provenance


def test_full_package_validates():
    snapshot, identity, provenance = _package()

    result = FingerprintValidationEngine.validate(
        snapshot,
        identity,
        provenance,
    )

    assert result.valid is True
    assert result.snapshot_valid is True
    assert result.identity_valid is True
    assert result.provenance_valid is True


def test_partial_validation_is_supported():
    snapshot = _snapshot()

    result = FingerprintValidationEngine.validate(
        snapshot
    )

    assert result.valid is True


def test_invalid_identity_fails():
    snapshot, identity, provenance = _package()

    tampered_identity = type(identity)(
        identity_version=identity.identity_version,
        schema_version=identity.schema_version,
        authority=identity.authority,
        algorithm=identity.algorithm,
        overall_fingerprint=identity.overall_fingerprint,
        identity_fingerprint="0" * 64,
    )

    result = FingerprintValidationEngine.validate(
        snapshot,
        tampered_identity,
        provenance,
    )

    assert result.valid is False


def test_validate_or_raise_fails_closed():
    snapshot, identity, provenance = _package()

    tampered_provenance = type(provenance)(
        provenance_version=provenance.provenance_version,
        source_schema_version=provenance.source_schema_version,
        source_authority=provenance.source_authority,
        source_algorithm=provenance.source_algorithm,
        source_fingerprint="0" * 64,
        identity_fingerprint=provenance.identity_fingerprint,
        provenance_fingerprint=provenance.provenance_fingerprint,
    )

    try:
        FingerprintValidationEngine.validate_or_raise(
            snapshot,
            identity,
            tampered_provenance,
        )
        assert False
    except FingerprintValidationIntegrityError:
        assert True