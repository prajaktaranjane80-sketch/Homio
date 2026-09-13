"""
REOS Diagnostic Contract
========================

Defines the stable diagnostic surface.

The contract intentionally describes the existing architecture instead of
creating a new architecture.
"""

from __future__ import annotations


SCHEMA_VERSION = "1.0"

DIAGNOSTIC_AUTHORITY = "OBSERVATIONAL_ONLY"

REQUIRED_CHECKS: tuple[str, ...] = (
    "CONTROL_CENTER",
    "STATE",
    "ARCHITECTURE",
    "AUTONOMY_ENGINE",
    "ACRL",
    "RUNTIME",
    "MISSION_CYCLE",
    "CHECKPOINT",
    "RECOVERY",
    "INTEGRATION",
)

FAIL_CLOSED_STATUSES = frozenset(
    {
        "BLOCKED",
    }
)


def validate_check_keys(keys: tuple[str, ...]) -> None:
    """
    Ensure the diagnostic surface does not silently lose a required layer.
    """

    missing = tuple(
        key
        for key in REQUIRED_CHECKS
        if key not in keys
    )

    if missing:
        raise ValueError(
            "Diagnostic contract incomplete: "
            + ", ".join(missing)
        )


def validate_unique_check_keys(keys: tuple[str, ...]) -> None:
    """
    Detect accidental duplicate health layers.
    """

    if len(keys) != len(set(keys)):
        raise ValueError(
            "Diagnostic contract contains duplicate check keys"
        )
