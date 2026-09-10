from __future__ import annotations


class SafeAuthorizationError(RuntimeError):
    """Base T18 authorization error."""


class SafeAuthorizationInputError(SafeAuthorizationError):
    """Raised when T18 input is structurally invalid."""


class SafeAuthorizationSecurityError(SafeAuthorizationError):
    """Raised when a T18 security boundary is violated."""


class SafeAuthorizationIntegrityError(SafeAuthorizationError):
    """Raised when bound evidence or fingerprints do not match."""


class SafeAuthorizationCompatibilityError(SafeAuthorizationError):
    """Raised when a T18 schema or upstream contract is incompatible."""


class SafeAuthorizationPolicyError(SafeAuthorizationError):
    """Raised when the T18 policy itself is invalid."""


__all__ = [
    "SafeAuthorizationError",
    "SafeAuthorizationInputError",
    "SafeAuthorizationSecurityError",
    "SafeAuthorizationIntegrityError",
    "SafeAuthorizationCompatibilityError",
    "SafeAuthorizationPolicyError",
]
