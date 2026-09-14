"""Read-only context verification helpers for REOS.

Authority remains the existing REOS Control Center and its canonical
data/state.json. This package does not create or replace any authority.
"""

from .control_plane import (
    CanonicalAuthorityResult,
    CanonicalAuthorityVerifier,
    verify_canonical_authority,
)

__all__ = [
    "CanonicalAuthorityResult",
    "CanonicalAuthorityVerifier",
    "verify_canonical_authority",
]
