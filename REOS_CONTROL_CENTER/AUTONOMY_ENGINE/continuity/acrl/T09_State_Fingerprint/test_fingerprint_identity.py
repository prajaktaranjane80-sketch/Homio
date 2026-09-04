from .fingerprint_identity import (
    FingerprintIdentityEngine,
    FingerprintIdentityValidationError,
)
from .state_integrity import (
    StateIntegrityEngine,
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


def test_identity_builds():
    identity = FingerprintIdentityEngine.build(
        _snapshot()
    )
    assert identity.identity_version == "T09-IDENTITY-1.0"


def test_identity_is_deterministic():
    snapshot = _snapshot()

    first = FingerprintIdentityEngine.build(
        snapshot
    )
    second = FingerprintIdentityEngine.build(
        snapshot
    )

    assert first == second


def test_identity_validates():
    identity = FingerprintIdentityEngine.build(
        _snapshot()
    )

    assert FingerprintIdentityEngine.validate(
        identity
    )


def test_tampered_identity_fails():
    identity = FingerprintIdentityEngine.build(
        _snapshot()
    )

    tampered = type(identity)(
        identity_version=identity.identity_version,
        schema_version=identity.schema_version,
        authority=identity.authority,
        algorithm=identity.algorithm,
        overall_fingerprint="0" * 64,
        identity_fingerprint=identity.identity_fingerprint,
    )

    try:
        FingerprintIdentityEngine.validate(
            tampered
        )
        assert False
    except FingerprintIdentityValidationError:
        assert True