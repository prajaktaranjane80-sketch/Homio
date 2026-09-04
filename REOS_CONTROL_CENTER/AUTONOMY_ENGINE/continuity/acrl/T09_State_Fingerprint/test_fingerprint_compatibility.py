import pytest

from .fingerprint_compatibility import (
    CompatibilityStatus,
    FingerprintCompatibilityEngine,
    FingerprintCompatibilityError,
    FingerprintCompatibilityValidationError,
)


def test_current_schema_is_supported():
    result = FingerprintCompatibilityEngine.check_schema(
        "1.0"
    )

    assert result.status == CompatibilityStatus.SUPPORTED
    assert result.accepted is True
    assert result.migration_required is False


def test_current_identity_is_supported():
    result = FingerprintCompatibilityEngine.check_identity(
        "T09-IDENTITY-1.0"
    )

    assert result.status == CompatibilityStatus.SUPPORTED
    assert result.accepted is True


def test_current_provenance_is_supported():
    result = FingerprintCompatibilityEngine.check_provenance(
        "T09-PROVENANCE-1.0"
    )

    assert result.status == CompatibilityStatus.SUPPORTED
    assert result.accepted is True


def test_unknown_schema_fails_closed():
    result = FingerprintCompatibilityEngine.check_schema(
        "99.0"
    )

    assert result.status == CompatibilityStatus.UNKNOWN
    assert result.accepted is False


def test_unknown_identity_fails_closed():
    result = FingerprintCompatibilityEngine.check_identity(
        "T09-IDENTITY-99.0"
    )

    assert result.status == CompatibilityStatus.UNKNOWN
    assert result.accepted is False


def test_empty_version_is_invalid():
    with pytest.raises(
        FingerprintCompatibilityValidationError
    ):
        FingerprintCompatibilityEngine.check_schema(
            ""
        )


def test_validate_all_accepts_current_versions():
    results = FingerprintCompatibilityEngine.validate_all(
        "1.0",
        "T09-IDENTITY-1.0",
        "T09-PROVENANCE-1.0",
    )

    assert len(results) == 3


def test_validate_all_rejects_unknown_version():
    with pytest.raises(
        FingerprintCompatibilityError
    ):
        FingerprintCompatibilityEngine.validate_all(
            "1.0",
            "UNKNOWN",
            "T09-PROVENANCE-1.0",
        )