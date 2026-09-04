"""ACRL T09 — Fingerprint Provenance.

Provides immutable provenance metadata for a T09 State Integrity snapshot.

Responsibilities:
- bind a fingerprint to its source snapshot
- preserve source identity and fingerprint
- preserve algorithm, authority and schema information
- provide deterministic provenance fingerprint
- reject provenance spoofing and tampering

This module is observational only.
It never mutates authoritative state.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .state_integrity import StateIntegritySnapshot
from .fingerprint_identity import FingerprintIdentity


class FingerprintProvenanceError(RuntimeError):
    """Base provenance error."""


class FingerprintProvenanceValidationError(
    FingerprintProvenanceError
):
    """Raised when provenance is invalid."""


@dataclass(frozen=True)
class FingerprintProvenance:
    """Immutable provenance record for a T09 fingerprint."""

    provenance_version: str
    source_schema_version: str
    source_authority: str
    source_algorithm: str
    source_fingerprint: str
    identity_fingerprint: str
    provenance_fingerprint: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provenance_version": self.provenance_version,
            "source_schema_version": self.source_schema_version,
            "source_authority": self.source_authority,
            "source_algorithm": self.source_algorithm,
            "source_fingerprint": self.source_fingerprint,
            "identity_fingerprint": self.identity_fingerprint,
            "provenance_fingerprint": self.provenance_fingerprint,
        }

    def verify(self) -> bool:
        payload = {
            "provenance_version": self.provenance_version,
            "source_schema_version": self.source_schema_version,
            "source_authority": self.source_authority,
            "source_algorithm": self.source_algorithm,
            "source_fingerprint": self.source_fingerprint,
            "identity_fingerprint": self.identity_fingerprint,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        expected = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return expected == self.provenance_fingerprint


class FingerprintProvenanceEngine:
    """Build and validate deterministic T09 provenance."""

    PROVENANCE_VERSION = "T09-PROVENANCE-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    @classmethod
    def _validate_snapshot(
        cls,
        snapshot: StateIntegritySnapshot,
    ) -> None:
        if not isinstance(
            snapshot,
            StateIntegritySnapshot,
        ):
            raise FingerprintProvenanceValidationError(
                "Input must be a StateIntegritySnapshot."
            )

        if snapshot.authority != cls.AUTHORITY:
            raise FingerprintProvenanceValidationError(
                "Fingerprint snapshot authority mismatch."
            )

        if snapshot.algorithm != cls.ALGORITHM:
            raise FingerprintProvenanceValidationError(
                "Unsupported fingerprint algorithm."
            )

        if not snapshot.overall_fingerprint:
            raise FingerprintProvenanceValidationError(
                "Source fingerprint is required."
            )

    @classmethod
    def _validate_identity(
        cls,
        identity: FingerprintIdentity,
    ) -> None:
        if not isinstance(
            identity,
            FingerprintIdentity,
        ):
            raise FingerprintProvenanceValidationError(
                "Input identity must be a FingerprintIdentity."
            )

        if identity.authority != cls.AUTHORITY:
            raise FingerprintProvenanceValidationError(
                "Fingerprint identity authority mismatch."
            )

        if identity.algorithm != cls.ALGORITHM:
            raise FingerprintProvenanceValidationError(
                "Fingerprint identity algorithm mismatch."
            )

        if not identity.verify():
            raise FingerprintProvenanceValidationError(
                "Fingerprint identity integrity verification failed."
            )

    @classmethod
    def build(
        cls,
        snapshot: StateIntegritySnapshot,
        identity: FingerprintIdentity,
    ) -> FingerprintProvenance:
        """Build immutable provenance from a valid snapshot and identity."""

        cls._validate_snapshot(snapshot)
        cls._validate_identity(identity)

        if identity.overall_fingerprint != snapshot.overall_fingerprint:
            raise FingerprintProvenanceValidationError(
                "Identity fingerprint does not match source snapshot."
            )

        payload = {
            "provenance_version": cls.PROVENANCE_VERSION,
            "source_schema_version": snapshot.schema_version,
            "source_authority": snapshot.authority,
            "source_algorithm": snapshot.algorithm,
            "source_fingerprint": snapshot.overall_fingerprint,
            "identity_fingerprint": identity.identity_fingerprint,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        provenance_fingerprint = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return FingerprintProvenance(
            provenance_version=cls.PROVENANCE_VERSION,
            source_schema_version=snapshot.schema_version,
            source_authority=snapshot.authority,
            source_algorithm=snapshot.algorithm,
            source_fingerprint=snapshot.overall_fingerprint,
            identity_fingerprint=identity.identity_fingerprint,
            provenance_fingerprint=provenance_fingerprint,
        )

    @classmethod
    def validate(
        cls,
        provenance: FingerprintProvenance,
    ) -> bool:
        """Validate provenance integrity and authority."""

        if not isinstance(
            provenance,
            FingerprintProvenance,
        ):
            raise FingerprintProvenanceValidationError(
                "Input must be a FingerprintProvenance."
            )

        if provenance.provenance_version != cls.PROVENANCE_VERSION:
            raise FingerprintProvenanceValidationError(
                "Unsupported provenance version."
            )

        if provenance.source_authority != cls.AUTHORITY:
            raise FingerprintProvenanceValidationError(
                "Provenance authority mismatch."
            )

        if provenance.source_algorithm != cls.ALGORITHM:
            raise FingerprintProvenanceValidationError(
                "Unsupported provenance algorithm."
            )

        if not provenance.source_fingerprint:
            raise FingerprintProvenanceValidationError(
                "Source fingerprint is required."
            )

        if not provenance.identity_fingerprint:
            raise FingerprintProvenanceValidationError(
                "Identity fingerprint is required."
            )

        if not provenance.verify():
            raise FingerprintProvenanceValidationError(
                "Provenance integrity verification failed."
            )

        return True


def build_fingerprint_provenance(
    snapshot: StateIntegritySnapshot,
    identity: FingerprintIdentity,
) -> FingerprintProvenance:
    """Convenience API for provenance creation."""

    return FingerprintProvenanceEngine.build(
        snapshot,
        identity,
    )


def validate_fingerprint_provenance(
    provenance: FingerprintProvenance,
) -> bool:
    """Convenience API for provenance validation."""

    return FingerprintProvenanceEngine.validate(
        provenance
    )


__all__ = [
    "FingerprintProvenance",
    "FingerprintProvenanceEngine",
    "FingerprintProvenanceError",
    "FingerprintProvenanceValidationError",
    "build_fingerprint_provenance",
    "validate_fingerprint_provenance",
]