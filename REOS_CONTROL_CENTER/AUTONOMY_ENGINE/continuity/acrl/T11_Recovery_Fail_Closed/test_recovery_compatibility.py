"""Tests for T11 compatibility."""

from __future__ import annotations

import pytest

from .recovery_compatibility import (
    RecoveryCompatibilityEngine,
    RecoveryCompatibilityError,
    RecoveryCompatibilityStatus,
)


def valid_versions() -> dict[str, str]:
    return {
        "schema_version": "1.0",
        "policy_version": "T11-POLICY-1.0",
        "identity_version": "T11-IDENTITY-1.0",
        "provenance_version": "T11-PROVENANCE-1.0",
    }


def test_current_versions_supported() -> None:
    status = RecoveryCompatibilityEngine.check(
        **valid_versions()
    )

    assert status == (
        RecoveryCompatibilityStatus.SUPPORTED
    )


def test_unknown_schema_is_incompatible() -> None:
    versions = valid_versions()
    versions["schema_version"] = "9.9"

    status = RecoveryCompatibilityEngine.check(
        **versions
    )

    assert status == (
        RecoveryCompatibilityStatus.INCOMPATIBLE
    )


def test_require_supported_accepts_current() -> None:
    assert RecoveryCompatibilityEngine.require_supported(
        **valid_versions()
    ) is True


def test_require_supported_rejects_old_version() -> None:
    versions = valid_versions()
    versions["policy_version"] = "T11-POLICY-0.1"

    with pytest.raises(RecoveryCompatibilityError):
        RecoveryCompatibilityEngine.require_supported(
            **versions
        )