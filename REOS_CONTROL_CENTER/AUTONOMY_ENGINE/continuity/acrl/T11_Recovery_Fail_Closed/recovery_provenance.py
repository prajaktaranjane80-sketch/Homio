"""ACRL T11 — Recovery provenance."""

from __future__ import annotations

from dataclasses import dataclass


class RecoveryProvenanceError(RuntimeError):
    """Base recovery provenance error."""


@dataclass(frozen=True)
class RecoveryProvenance:
    source_layer: str
    source_identity: str
    source_fingerprint: str
    recovery_policy_version: str
    authority: str
    provenance_version: str = "T11-PROVENANCE-1.0"

    def to_dict(self) -> dict[str, str]:
        return {
            "provenance_version": self.provenance_version,
            "source_layer": self.source_layer,
            "source_identity": self.source_identity,
            "source_fingerprint": self.source_fingerprint,
            "recovery_policy_version": (
                self.recovery_policy_version
            ),
            "authority": self.authority,
        }


class RecoveryProvenanceEngine:
    """Validates where a recovery decision came from."""

    PROVENANCE_VERSION = "T11-PROVENANCE-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALLOWED_SOURCE_LAYERS = frozenset(
        {
            "T10_DRIFT_DETECTION",
            "T09_STATE_FINGERPRINT",
        }
    )

    @classmethod
    def build(
        cls,
        *,
        source_layer: str,
        source_identity: str,
        source_fingerprint: str,
        recovery_policy_version: str,
    ) -> RecoveryProvenance:
        if source_layer not in cls.ALLOWED_SOURCE_LAYERS:
            raise RecoveryProvenanceError(
                "Unsupported recovery source layer."
            )

        if not source_identity.strip():
            raise RecoveryProvenanceError(
                "Source identity cannot be empty."
            )

        if len(source_fingerprint) != 64:
            raise RecoveryProvenanceError(
                "Invalid source fingerprint."
            )

        if not recovery_policy_version.strip():
            raise RecoveryProvenanceError(
                "Recovery policy version cannot be empty."
            )

        return RecoveryProvenance(
            source_layer=source_layer,
            source_identity=source_identity,
            source_fingerprint=source_fingerprint,
            recovery_policy_version=(
                recovery_policy_version
            ),
            authority=cls.AUTHORITY,
        )

    @classmethod
    def validate(
        cls,
        provenance: RecoveryProvenance,
    ) -> bool:
        if not isinstance(
            provenance,
            RecoveryProvenance,
        ):
            raise RecoveryProvenanceError(
                "Invalid recovery provenance."
            )

        if provenance.provenance_version != (
            cls.PROVENANCE_VERSION
        ):
            raise RecoveryProvenanceError(
                "Unsupported provenance version."
            )

        if provenance.authority != cls.AUTHORITY:
            raise RecoveryProvenanceError(
                "Invalid provenance authority."
            )

        if provenance.source_layer not in (
            cls.ALLOWED_SOURCE_LAYERS
        ):
            raise RecoveryProvenanceError(
                "Unsupported provenance source layer."
            )

        if len(provenance.source_fingerprint) != 64:
            raise RecoveryProvenanceError(
                "Invalid provenance fingerprint."
            )

        return True


__all__ = [
    "RecoveryProvenance",
    "RecoveryProvenanceEngine",
    "RecoveryProvenanceError",
]