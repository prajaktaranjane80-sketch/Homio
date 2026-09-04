from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResumeProvenance:
    provenance_version: str
    source_layer: str
    source_identity: str
    source_fingerprint: str
    policy_version: str
    authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_version": self.provenance_version,
            "source_layer": self.source_layer,
            "source_identity": self.source_identity,
            "source_fingerprint": self.source_fingerprint,
            "policy_version": self.policy_version,
            "authority": self.authority,
        }


class ResumeProvenanceEngine:
    PROVENANCE_VERSION = "T12-PROVENANCE-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALLOWED_SOURCE_LAYERS = frozenset(
        {
            "T09_STATE_FINGERPRINT",
            "T10_DRIFT_DETECTION",
            "T11_RECOVERY_FAIL_CLOSED",
        }
    )

    @classmethod
    def build(
        cls,
        source_layer: str,
        source_identity: str,
        source_fingerprint: str,
        policy_version: str,
    ) -> ResumeProvenance:
        if source_layer not in cls.ALLOWED_SOURCE_LAYERS:
            raise ValueError("Unsupported provenance source layer.")

        if not source_identity:
            raise ValueError("Source identity is required.")

        if not isinstance(source_fingerprint, str):
            raise TypeError("Source fingerprint must be a string.")

        if len(source_fingerprint) != 64:
            raise ValueError("Source fingerprint must be SHA-256.")

        if not policy_version:
            raise ValueError("Policy version is required.")

        return ResumeProvenance(
            provenance_version=cls.PROVENANCE_VERSION,
            source_layer=source_layer,
            source_identity=source_identity,
            source_fingerprint=source_fingerprint,
            policy_version=policy_version,
            authority=cls.AUTHORITY,
        )

    @classmethod
    def validate(cls, provenance: ResumeProvenance) -> bool:
        if not isinstance(provenance, ResumeProvenance):
            return False

        if provenance.provenance_version != cls.PROVENANCE_VERSION:
            return False

        if provenance.authority != cls.AUTHORITY:
            return False

        if provenance.source_layer not in cls.ALLOWED_SOURCE_LAYERS:
            return False

        if not provenance.source_identity:
            return False

        if len(provenance.source_fingerprint) != 64:
            return False

        if not provenance.policy_version:
            return False

        return True