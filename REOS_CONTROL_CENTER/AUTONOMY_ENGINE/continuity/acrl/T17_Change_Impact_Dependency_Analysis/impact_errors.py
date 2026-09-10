from __future__ import annotations


class ChangeImpactError(RuntimeError):
    """Base error for T17 change-impact analysis."""


class ChangeImpactValidationError(ChangeImpactError):
    """Raised when T17 input or report validation fails."""


class ChangeImpactSecurityError(ChangeImpactError):
    """Raised when a T17 security boundary is violated."""


class ChangeImpactIntegrityError(ChangeImpactError):
    """Raised when T17 report integrity validation fails."""


class ChangeImpactCompatibilityError(ChangeImpactError):
    """Raised when an unsupported T17 schema is encountered."""


__all__ = [
    "ChangeImpactError",
    "ChangeImpactValidationError",
    "ChangeImpactSecurityError",
    "ChangeImpactIntegrityError",
    "ChangeImpactCompatibilityError",
]
