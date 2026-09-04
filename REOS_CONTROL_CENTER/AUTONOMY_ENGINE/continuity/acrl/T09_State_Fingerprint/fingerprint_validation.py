"""ACRL T09 — Fingerprint Validation.

Central validation boundary for T09 fingerprint artifacts.

This layer validates:
- snapshot structure
- authority
- schema version
- algorithm
- required components
- fingerprint integrity
- identity
- provenance

No mutation is performed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .state_integrity import (
    StateIntegrityEngine,
    StateIntegritySnapshot,
)
from .fingerprint_identity import (
    FingerprintIdentity,
    FingerprintIdentityEngine,
)
from .fingerprint_provenance import (
    FingerprintProvenance,
    FingerprintProvenanceEngine,
)


class FingerprintValidationError(RuntimeError):
    """Base fingerprint validation error."""


class FingerprintValidationAuthorityError(
    FingerprintValidationError
):
    """Raised when authority is invalid."""


class FingerprintValidationIntegrityError(
    FingerprintValidationError
):
    """Raised when integrity validation fails."""


@dataclass(frozen=True)
class FingerprintValidationResult:
    """Immutable machine-readable validation result."""

    valid: bool
    authority_valid: bool
    snapshot_valid: bool
    identity_valid: bool
    provenance_valid: bool
    schema_version: str
    algorithm: str
    errors: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "authority_valid": self.authority_valid,
            "snapshot_valid": self.snapshot_valid,
            "identity_valid": self.identity_valid,
            "provenance_valid": self.provenance_valid,
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "errors": list(self.errors),
        }


class FingerprintValidationEngine:
    """Validate all T09 fingerprint layers."""

    AUTHORITY = "REOS_CONTROL_CENTER"
    SUPPORTED_SCHEMA_VERSION = "1.0"
    SUPPORTED_ALGORITHM = "sha256"

    @classmethod
    def validate(
        cls,
        snapshot: StateIntegritySnapshot,
        identity: FingerprintIdentity | None = None,
        provenance: FingerprintProvenance | None = None,
    ) -> FingerprintValidationResult:
        """Validate a complete T09 fingerprint package."""

        errors: list[str] = []

        authority_valid = False
        snapshot_valid = False
        identity_valid = identity is None
        provenance_valid = provenance is None

        schema_version = ""
        algorithm = ""

        if not isinstance(
            snapshot,
            StateIntegritySnapshot,
        ):
            errors.append(
                "Snapshot must be a StateIntegritySnapshot."
            )
        else:
            schema_version = snapshot.schema_version
            algorithm = snapshot.algorithm

            if snapshot.authority != cls.AUTHORITY:
                errors.append(
                    "Snapshot authority mismatch."
                )
            else:
                authority_valid = True

            if (
                snapshot.schema_version
                != cls.SUPPORTED_SCHEMA_VERSION
            ):
                errors.append(
                    "Unsupported snapshot schema version."
                )

            if (
                snapshot.algorithm
                != cls.SUPPORTED_ALGORITHM
            ):
                errors.append(
                    "Unsupported snapshot algorithm."
                )

            try:
                StateIntegrityEngine.verify_or_raise(
                    snapshot,
                    snapshot.components,
                )
                snapshot_valid = True
            except Exception as exc:
                errors.append(
                    "Snapshot integrity validation failed: "
                    f"{exc}"
                )

        if identity is not None:
            try:
                FingerprintIdentityEngine.validate(
                    identity
                )

                if (
                    isinstance(
                        snapshot,
                        StateIntegritySnapshot,
                    )
                    and identity.overall_fingerprint
                    != snapshot.overall_fingerprint
                ):
                    raise FingerprintValidationIntegrityError(
                        "Identity does not match snapshot."
                    )

                identity_valid = True

            except Exception as exc:
                identity_valid = False
                errors.append(
                    f"Identity validation failed: {exc}"
                )

        if provenance is not None:
            try:
                FingerprintProvenanceEngine.validate(
                    provenance
                )

                if (
                    isinstance(
                        snapshot,
                        StateIntegritySnapshot,
                    )
                    and provenance.source_fingerprint
                    != snapshot.overall_fingerprint
                ):
                    raise FingerprintValidationIntegrityError(
                        "Provenance does not match snapshot."
                    )

                if (
                    identity is not None
                    and provenance.identity_fingerprint
                    != identity.identity_fingerprint
                ):
                    raise FingerprintValidationIntegrityError(
                        "Provenance does not match identity."
                    )

                provenance_valid = True

            except Exception as exc:
                provenance_valid = False
                errors.append(
                    f"Provenance validation failed: {exc}"
                )

        valid = (
            authority_valid
            and snapshot_valid
            and identity_valid
            and provenance_valid
            and not errors
        )

        return FingerprintValidationResult(
            valid=valid,
            authority_valid=authority_valid,
            snapshot_valid=snapshot_valid,
            identity_valid=identity_valid,
            provenance_valid=provenance_valid,
            schema_version=schema_version,
            algorithm=algorithm,
            errors=tuple(errors),
        )

    @classmethod
    def validate_or_raise(
        cls,
        snapshot: StateIntegritySnapshot,
        identity: FingerprintIdentity | None = None,
        provenance: FingerprintProvenance | None = None,
    ) -> FingerprintValidationResult:
        """Fail closed when the T09 package is invalid."""

        result = cls.validate(
            snapshot,
            identity,
            provenance,
        )

        if not result.valid:
            raise FingerprintValidationIntegrityError(
                "; ".join(result.errors)
            )

        return result


def validate_fingerprint_package(
    snapshot: StateIntegritySnapshot,
    identity: FingerprintIdentity | None = None,
    provenance: FingerprintProvenance | None = None,
) -> FingerprintValidationResult:
    """Convenience API."""

    return FingerprintValidationEngine.validate(
        snapshot,
        identity,
        provenance,
    )


__all__ = [
    "FingerprintValidationError",
    "FingerprintValidationAuthorityError",
    "FingerprintValidationIntegrityError",
    "FingerprintValidationResult",
    "FingerprintValidationEngine",
    "validate_fingerprint_package",
]