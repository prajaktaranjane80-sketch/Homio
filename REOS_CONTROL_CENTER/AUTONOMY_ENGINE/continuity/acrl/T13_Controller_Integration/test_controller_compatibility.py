import pytest

from .controller_compatibility import (
    ControllerCompatibilityEngine,
    ControllerCompatibilityError,
    ControllerCompatibilityStatus,
)


def test_current_schema_is_supported():
    status = ControllerCompatibilityEngine.schema_status("1.0")

    assert status is ControllerCompatibilityStatus.SUPPORTED


def test_current_policy_is_supported():
    status = ControllerCompatibilityEngine.policy_status(
        "T13-POLICY-1.0"
    )

    assert status is ControllerCompatibilityStatus.SUPPORTED


def test_current_identity_is_supported():
    status = ControllerCompatibilityEngine.identity_status(
        "T13-IDENTITY-1.0"
    )

    assert status is ControllerCompatibilityStatus.SUPPORTED


def test_current_provenance_is_supported():
    status = ControllerCompatibilityEngine.provenance_status(
        "T13-PROVENANCE-1.0"
    )

    assert status is ControllerCompatibilityStatus.SUPPORTED


def test_empty_schema_is_unknown():
    status = ControllerCompatibilityEngine.schema_status("")

    assert status is ControllerCompatibilityStatus.UNKNOWN


def test_unknown_schema_is_incompatible():
    status = ControllerCompatibilityEngine.schema_status("99.0")

    assert status is ControllerCompatibilityStatus.INCOMPATIBLE


def test_require_supported_accepts_supported():
    ControllerCompatibilityEngine.require_supported(
        ControllerCompatibilityStatus.SUPPORTED
    )


def test_require_supported_rejects_unknown():
    with pytest.raises(ControllerCompatibilityError):
        ControllerCompatibilityEngine.require_supported(
            ControllerCompatibilityStatus.UNKNOWN
        )


def test_require_supported_rejects_incompatible():
    with pytest.raises(ControllerCompatibilityError):
        ControllerCompatibilityEngine.require_supported(
            ControllerCompatibilityStatus.INCOMPATIBLE
        )


def test_migratable_is_compatible():
    assert ControllerCompatibilityEngine.is_compatible(
        ControllerCompatibilityStatus.MIGRATABLE
    ) is True


def test_unknown_is_not_compatible():
    assert ControllerCompatibilityEngine.is_compatible(
        ControllerCompatibilityStatus.UNKNOWN
    ) is False