"""ACRL T09 — Fingerprint Registry.

Immutable registry for validated T09 fingerprint artifacts.

The registry is not an authoritative state store.
It provides deterministic lookup and replay-safe registration.
"""

from __future__ import annotations

from dataclasses import dataclass

from .state_integrity import StateIntegritySnapshot
from .fingerprint_identity import FingerprintIdentity
from .fingerprint_provenance import FingerprintProvenance
from .fingerprint_validation import (
    FingerprintValidationEngine,
)


class FingerprintRegistryError(RuntimeError):
    """Base registry error."""


class FingerprintRegistryValidationError(
    FingerprintRegistryError
):
    """Raised when registry input is invalid."""


class FingerprintRegistryConflictError(
    FingerprintRegistryError
):
    """Raised when a fingerprint registration conflicts."""


@dataclass(frozen=True)
class FingerprintRegistryEntry:
    """Immutable validated fingerprint entry."""

    fingerprint: str
    identity_fingerprint: str
    provenance_fingerprint: str
    schema_version: str
    authority: str

    def to_dict(self) -> dict[str, str]:
        return {
            "fingerprint": self.fingerprint,
            "identity_fingerprint": self.identity_fingerprint,
            "provenance_fingerprint": self.provenance_fingerprint,
            "schema_version": self.schema_version,
            "authority": self.authority,
        }


@dataclass(frozen=True)
class FingerprintRegistry:
    """Immutable registry snapshot."""

    entries: tuple[FingerprintRegistryEntry, ...]

    def to_dict(self) -> dict:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }

    def get(
        self,
        fingerprint: str,
    ) -> FingerprintRegistryEntry | None:
        for entry in self.entries:
            if entry.fingerprint == fingerprint:
                return entry
        return None

    def contains(
        self,
        fingerprint: str,
    ) -> bool:
        return self.get(fingerprint) is not None


class FingerprintRegistryEngine:
    """Build immutable registry projections."""

    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def register(
        cls,
        registry: FingerprintRegistry,
        snapshot: StateIntegritySnapshot,
        identity: FingerprintIdentity,
        provenance: FingerprintProvenance,
    ) -> FingerprintRegistry:
        if not isinstance(
            registry,
            FingerprintRegistry,
        ):
            raise FingerprintRegistryValidationError(
                "Registry must be a FingerprintRegistry."
            )

        FingerprintValidationEngine.validate_or_raise(
            snapshot,
            identity,
            provenance,
        )

        if snapshot.authority != cls.AUTHORITY:
            raise FingerprintRegistryValidationError(
                "Registry authority mismatch."
            )

        entry = FingerprintRegistryEntry(
            fingerprint=snapshot.overall_fingerprint,
            identity_fingerprint=identity.identity_fingerprint,
            provenance_fingerprint=provenance.provenance_fingerprint,
            schema_version=snapshot.schema_version,
            authority=snapshot.authority,
        )

        existing = registry.get(
            entry.fingerprint
        )

        if existing is not None:
            if existing == entry:
                return registry

            raise FingerprintRegistryConflictError(
                "Fingerprint already exists with conflicting metadata."
            )

        return FingerprintRegistry(
            entries=registry.entries + (entry,)
        )

    @classmethod
    def empty(cls) -> FingerprintRegistry:
        return FingerprintRegistry(
            entries=()
        )


def register_fingerprint(
    registry: FingerprintRegistry,
    snapshot: StateIntegritySnapshot,
    identity: FingerprintIdentity,
    provenance: FingerprintProvenance,
) -> FingerprintRegistry:
    """Convenience registration API."""

    return FingerprintRegistryEngine.register(
        registry,
        snapshot,
        identity,
        provenance,
    )


__all__ = [
    "FingerprintRegistry",
    "FingerprintRegistryEntry",
    "FingerprintRegistryError",
    "FingerprintRegistryValidationError",
    "FingerprintRegistryConflictError",
    "FingerprintRegistryEngine",
    "register_fingerprint",
]