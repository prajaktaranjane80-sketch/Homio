import pytest

from reconciliation_guard import validate_authority


def test_missing_continuity_is_rejected():
    with pytest.raises(PermissionError):
        validate_authority(
            continuity_fingerprint="",
            evidence_fingerprint="E1",
        )


def test_missing_evidence_is_rejected():
    with pytest.raises(PermissionError):
        validate_authority(
            continuity_fingerprint="C1",
            evidence_fingerprint="",
        )
