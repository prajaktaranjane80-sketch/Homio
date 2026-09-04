"""ACRL T09 — Fingerprint Identity.

Additive identity layer for T09 State Fingerprint.

Responsibilities:
- identify one fingerprint snapshot deterministically
- bind identity to schema, authority, algorithm and fingerprint
- provide immutable machine-readable identity
- prevent identity spoofing through validation

Architecture rules:
- T01-T08 remain read-only dependencies.
- T09 does not create authority.
- T09 does not mutate authoritative state.
- Identity is derived from an existing valid T09 snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .state_integrity import StateIntegritySnapshot


class FingerprintIdentityError(RuntimeError):
    """Base fingerprint identity error."""


class FingerprintIdentityValidationError(FingerprintIdentityError):
    """Raised when fingerprint identity input is invalid."""


@dataclass(frozen=True)
class FingerprintIdentity:
    """Immutable identity of a T09 fingerprint snapshot."""

    identity_version: str
    schema_version: str
    authority: str
    algorithm: str
    overall_fingerprint: str
    identity_fingerprint: str

    def to_dict(self) -> dict[str, str]:
        return {
            "identity_version": self.identity_version,
            "schema_version": self.schema_version,
            "authority": self.authority,
            "algorithm": self.algorithm,
            "overall_fingerprint": self.overall_fingerprint,
            "identity_fingerprint": self.identity_fingerprint,
        }

    def verify(self) -> bool:
        payload = {
            "identity_version": self.identity_version,
            "schema_version": self.schema_version,
            "authority": self.authority,
            "algorithm": self.algorithm,
            "overall_fingerprint": self.overall_fingerprint,
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

        return expected == self.identity_fingerprint


class FingerprintIdentityEngine:
    """Build and validate deterministic fingerprint identity."""

    IDENTITY_VERSION = "T09-IDENTITY-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def _validate_snapshot(
        cls,
        snapshot: StateIntegritySnapshot,
    ) -> None:
        if not isinstance(
            snapshot,
            StateIntegritySnapshot,
        ):
            raise FingerprintIdentityValidationError(
                "Input must be a StateIntegritySnapshot."
            )

        if snapshot.authority != cls.AUTHORITY:
            raise FingerprintIdentityValidationError(
                "Fingerprint snapshot authority mismatch."
            )

        if not snapshot.overall_fingerprint:
            raise FingerprintIdentityValidationError(
                "Overall fingerprint is required."
            )

        if snapshot.algorithm != "sha256":
            raise FingerprintIdentityValidationError(
                "Unsupported fingerprint algorithm."
            )

    @classmethod
    def _identity_payload(
        cls,
        snapshot: StateIntegritySnapshot,
    ) -> dict[str, str]:
        return {
            "identity_version": cls.IDENTITY_VERSION,
            "schema_version": snapshot.schema_version,
            "authority": snapshot.authority,
            "algorithm": snapshot.algorithm,
            "overall_fingerprint": snapshot.overall_fingerprint,
        }

    @classmethod
    def build(
        cls,
        snapshot: StateIntegritySnapshot,
    ) -> FingerprintIdentity:
        """Build deterministic identity from a valid T09 snapshot."""

        cls._validate_snapshot(snapshot)

        payload = cls._identity_payload(snapshot)

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        identity_fingerprint = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return FingerprintIdentity(
            identity_version=cls.IDENTITY_VERSION,
            schema_version=snapshot.schema_version,
            authority=snapshot.authority,
            algorithm=snapshot.algorithm,
            overall_fingerprint=snapshot.overall_fingerprint,
            identity_fingerprint=identity_fingerprint,
        )

    @classmethod
    def validate(
        cls,
        identity: FingerprintIdentity,
    ) -> bool:
        """Validate fingerprint identity integrity."""

        if not isinstance(
            identity,
            FingerprintIdentity,
        ):
            raise FingerprintIdentityValidationError(
                "Input must be a FingerprintIdentity."
            )

        if identity.identity_version != cls.IDENTITY_VERSION:
            raise FingerprintIdentityValidationError(
                "Unsupported fingerprint identity version."
            )

        if identity.authority != cls.AUTHORITY:
            raise FingerprintIdentityValidationError(
                "Fingerprint identity authority mismatch."
            )

        if identity.algorithm != "sha256":
            raise FingerprintIdentityValidationError(
                "Unsupported fingerprint algorithm."
            )

        if not identity.verify():
            raise FingerprintIdentityValidationError(
                "Fingerprint identity integrity verification failed."
            )

        return True


def build_fingerprint_identity(
    snapshot: StateIntegritySnapshot,
) -> FingerprintIdentity:
    """Convenience API for fingerprint identity creation."""

    return FingerprintIdentityEngine.build(snapshot)


def validate_fingerprint_identity(
    identity: FingerprintIdentity,
) -> bool:
    """Convenience API for fingerprint identity validation."""

    return FingerprintIdentityEngine.validate(identity)


__all__ = [
    "FingerprintIdentity",
    "FingerprintIdentityEngine",
    "FingerprintIdentityError",
    "FingerprintIdentityValidationError",
    "build_fingerprint_identity",
    "validate_fingerprint_identity",
]