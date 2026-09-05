"""ACRL T13 — Controller Integration Provenance."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControllerProvenance:
    source_layer: str
    source_identity: str
    source_fingerprint: str
    policy_version: str
    authority: str
    provenance_version: str = "T13-PROVENANCE-1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_version": self.provenance_version,
            "source_layer": self.source_layer,
            "source_identity": self.source_identity,
            "source_fingerprint": self.source_fingerprint,
            "policy_version": self.policy_version,
            "authority": self.authority,
        }


class ControllerProvenanceEngine:
    PROVENANCE_VERSION = "T13-PROVENANCE-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    ALLOWED_SOURCE_LAYERS = {
        "T09_STATE_FINGERPRINT",
        "T10_DRIFT_DETECTION",
        "T11_RECOVERY_FAIL_CLOSED",
        "T12_RESUME_SAFETY",
    }

    @classmethod
    def build(
        cls,
        source_layer: str,
        source_identity: str,
        source_fingerprint: str,
        policy_version: str,
    ) -> ControllerProvenance:
        provenance = ControllerProvenance(
            source_layer=source_layer,
            source_identity=source_identity,
            source_fingerprint=source_fingerprint,
            policy_version=policy_version,
            authority=cls.AUTHORITY,
            provenance_version=cls.PROVENANCE_VERSION,
        )

        cls.validate(provenance)
        return provenance

    @classmethod
    def validate(cls, provenance: ControllerProvenance) -> bool:
        if not isinstance(provenance, ControllerProvenance):
            raise TypeError(
                "provenance must be a ControllerProvenance."
            )

        if provenance.provenance_version != cls.PROVENANCE_VERSION:
            raise ValueError("Unsupported T13 provenance version.")

        if provenance.authority != cls.AUTHORITY:
            raise ValueError("Invalid provenance authority.")

        if provenance.source_layer not in cls.ALLOWED_SOURCE_LAYERS:
            raise ValueError(
                f"Unsupported T13 provenance source: "
                f"{provenance.source_layer}"
            )

        if not isinstance(provenance.source_identity, str):
            raise ValueError("Invalid provenance source identity.")

        if (
            not isinstance(provenance.source_fingerprint, str)
            or len(provenance.source_fingerprint) != 64
        ):
            raise ValueError("Invalid provenance source fingerprint.")

        if not isinstance(provenance.policy_version, str):
            raise ValueError("Invalid provenance policy version.")

        return True