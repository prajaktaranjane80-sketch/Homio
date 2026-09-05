import pytest

from .controller_provenance import ControllerProvenanceEngine


def test_valid_t12_provenance():
    provenance = ControllerProvenanceEngine.build(
        source_layer="T12_RESUME_SAFETY",
        source_identity="T12-IDENTITY-001",
        source_fingerprint="a" * 64,
        policy_version="T13-POLICY-1.0",
    )

    assert ControllerProvenanceEngine.validate(provenance) is True


def test_all_allowed_sources_are_accepted():
    for source in (
        "T09_STATE_FINGERPRINT",
        "T10_DRIFT_DETECTION",
        "T11_RECOVERY_FAIL_CLOSED",
        "T12_RESUME_SAFETY",
    ):
        provenance = ControllerProvenanceEngine.build(
            source_layer=source,
            source_identity="IDENTITY",
            source_fingerprint="a" * 64,
            policy_version="T13-POLICY-1.0",
        )

        assert ControllerProvenanceEngine.validate(provenance) is True


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError):
        ControllerProvenanceEngine.build(
            source_layer="UNKNOWN_LAYER",
            source_identity="IDENTITY",
            source_fingerprint="a" * 64,
            policy_version="T13-POLICY-1.0",
        )


def test_invalid_fingerprint_is_rejected():
    with pytest.raises(ValueError):
        ControllerProvenanceEngine.build(
            source_layer="T12_RESUME_SAFETY",
            source_identity="IDENTITY",
            source_fingerprint="invalid",
            policy_version="T13-POLICY-1.0",
        )


def test_invalid_authority_is_rejected():
    provenance = ControllerProvenanceEngine.build(
        source_layer="T12_RESUME_SAFETY",
        source_identity="IDENTITY",
        source_fingerprint="a" * 64,
        policy_version="T13-POLICY-1.0",
    )

    tampered = type(provenance)(
        source_layer=provenance.source_layer,
        source_identity=provenance.source_identity,
        source_fingerprint=provenance.source_fingerprint,
        policy_version=provenance.policy_version,
        authority="FAKE_AUTHORITY",
        provenance_version=provenance.provenance_version,
    )

    with pytest.raises(ValueError):
        ControllerProvenanceEngine.validate(tampered)
