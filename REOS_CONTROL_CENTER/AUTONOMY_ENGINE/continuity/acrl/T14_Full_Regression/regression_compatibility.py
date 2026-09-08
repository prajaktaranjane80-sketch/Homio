"""ACRL T14 compatibility rules."""
from __future__ import annotations
from enum import Enum


class CompatibilityStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    MIGRATABLE = "MIGRATABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


def compare_schema(expected: str, actual: str) -> CompatibilityStatus:
    if expected == actual:
        return CompatibilityStatus.SUPPORTED
    if expected.split(".", 1)[0] == actual.split(".", 1)[0]:
        return CompatibilityStatus.MIGRATABLE
    return CompatibilityStatus.INCOMPATIBLE
