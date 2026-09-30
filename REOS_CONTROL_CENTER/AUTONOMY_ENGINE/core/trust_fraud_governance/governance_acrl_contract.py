"""CORE-007 Point 11 — ACRL integration contract.

This module defines the Trust/Fraud/Governance boundary with the existing
ACRL integration authority owned by CORE-002 / ACRL.

It does NOT:
- store domain state,
- replace ACRL,
- own checkpoints,
- create a second recovery engine,
- mutate Control Center state.

CORE-007 describes what must be reconstructed and how the reconstructed
material is verified. ACRL remains the reconstruction/recovery authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping
from uuid import UUID

from ..contract_primitives import (
    canonicalize,
    fingerprint,
    require_positive_version,
    require_same_scope,
)
from ..event_platform.event_acrl_contract import (
    ACRLIntegrationBoundary,
)


class GovernanceACRLError(ValueError):
    """Base CORE-007 ACRL contract error."""


class GovernanceACRLScopeError(GovernanceACRLError):
    """Raised when reconstructed material crosses tenant scope."""


class GovernanceACRLIntegrityError(GovernanceACRLError):
    """Raised when reconstructed material fails integrity validation."""


class GovernanceACRLCheckpointError(GovernanceACRLError):
    """Raised when checkpoint metadata is invalid."""


class GovernanceACRLArtifact(str, Enum):
    TRUST_SIGNAL = "TRUST_SIGNAL"
    FRAUD_SIGNAL = "FRAUD_SIGNAL"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    GOVERNANCE_RULE = "GOVERNANCE_RULE"
    GOVERNANCE_DECISION = "GOVERNANCE_DECISION"
    GOVERNANCE_EVIDENCE = "GOVERNANCE_EVIDENCE"


@dataclass(frozen=True, slots=True)
class GovernanceACRLArtifactDescriptor:
    """Immutable reconstruction descriptor for a CORE-007 artifact."""

    artifact_id: str
    artifact_type: GovernanceACRLArtifact
    tenant_id: str
    contract_key: str
    version: int
    fingerprint: str
    provenance_reference: str
    evidence_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "artifact_id",
            "tenant_id",
            "contract_key",
            "fingerprint",
            "provenance_reference",
        ):
            value = getattr(self, name)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise GovernanceACRLError(
                    f"{name} must be non-empty text."
                )

        require_positive_version(
            self.version,
            field_name="version",
        )

        normalized = tuple(
            dict.fromkeys(
                ref.strip()
                for ref in self.evidence_references
                if isinstance(ref, str)
                and ref.strip()
            )
        )

        object.__setattr__(
            self,
            "evidence_references",
            normalized,
        )

    @property
    def identity_key(
        self,
    ) -> tuple[str, str, str]:
        return (
            self.tenant_id,
            self.artifact_type.value,
            self.artifact_id,
        )

    def assert_scope(
        self,
        tenant_id: str,
    ) -> None:
        try:
            require_same_scope(
                self.tenant_id,
                tenant_id,
                field_name="tenant_id",
            )
        except Exception as exc:
            raise GovernanceACRLScopeError(
                "CORE-007 ACRL artifact crossed tenant scope."
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "tenant_id": self.tenant_id,
            "contract_key": self.contract_key,
            "version": self.version,
            "fingerprint": self.fingerprint,
            "provenance_reference": (
                self.provenance_reference
            ),
            "evidence_references": list(
                self.evidence_references
            ),
        }


@dataclass(frozen=True, slots=True)
class GovernanceACRLCheckpoint:
    """Recovery position supplied by ACRL.

    CORE-007 does not persist or advance this checkpoint.
    """

    checkpoint_id: str
    tenant_id: str
    sequence: int
    event_id: UUID

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.checkpoint_id,
                str,
            )
            or not self.checkpoint_id.strip()
        ):
            raise GovernanceACRLCheckpointError(
                "checkpoint_id is required."
            )

        if (
            not isinstance(
                self.tenant_id,
                str,
            )
            or not self.tenant_id.strip()
        ):
            raise GovernanceACRLError(
                "tenant_id is required."
            )

        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 0
        ):
            raise GovernanceACRLCheckpointError(
                "sequence must be an integer >= 0."
            )

        if not isinstance(
            self.event_id,
            UUID,
        ):
            raise GovernanceACRLCheckpointError(
                "event_id must be UUID."
            )


class GovernanceACRLContract:
    """CORE-007 adapter over the existing ACRL boundary."""

    def __init__(
        self,
        boundary: ACRLIntegrationBoundary,
    ) -> None:
        if not isinstance(
            boundary,
            ACRLIntegrationBoundary,
        ):
            raise TypeError(
                "boundary must be ACRLIntegrationBoundary."
            )

        self._boundary = boundary

    def dependencies(
        self,
        contract_key: str,
    ) -> tuple[str, ...]:
        return self._boundary.dependencies(
            contract_key
        )

    def drift_detected(
        self,
        *,
        expected_fingerprint: str,
        actual_fingerprint: str,
    ) -> bool:
        return self._boundary.drift_detected(
            expected_fingerprint=expected_fingerprint,
            actual_fingerprint=actual_fingerprint,
        )

    def reconstruct(
        self,
        *,
        event_id: UUID,
        descriptor: GovernanceACRLArtifactDescriptor,
    ) -> Mapping[str, Any]:
        """Reconstruct through ACRL and verify scope/integrity."""

        result = dict(
            self._boundary.reconstruct_event(
                event_id
            )
        )

        reconstructed_tenant = str(
            result.get("tenant_id", "")
        ).strip()

        if reconstructed_tenant:
            descriptor.assert_scope(
                reconstructed_tenant
            )

        supplied_fingerprint = str(
            result.get("fingerprint")
            or result.get("immutable_fingerprint")
            or ""
        ).strip()

        if supplied_fingerprint:
            if (
                supplied_fingerprint
                != descriptor.fingerprint
            ):
                raise GovernanceACRLIntegrityError(
                    "Reconstructed CORE-007 artifact "
                    "fingerprint differs from descriptor."
                )

            return result

        derived_fingerprint = fingerprint(
            canonicalize(result)
        )

        if (
            derived_fingerprint
            != descriptor.fingerprint
        ):
            raise GovernanceACRLIntegrityError(
                "Reconstructed CORE-007 artifact "
                "does not match descriptor fingerprint."
            )

        return result

    def reconstruct_signal(
        self,
        *,
        event_id: UUID,
        descriptor: GovernanceACRLArtifactDescriptor,
    ) -> Mapping[str, Any]:
        self._require_type(
            descriptor,
            GovernanceACRLArtifact.TRUST_SIGNAL,
        )

        return self.reconstruct(
            event_id=event_id,
            descriptor=descriptor,
        )

    def reconstruct_fraud_signal(
        self,
        *,
        event_id: UUID,
        descriptor: GovernanceACRLArtifactDescriptor,
    ) -> Mapping[str, Any]:
        self._require_type(
            descriptor,
            GovernanceACRLArtifact.FRAUD_SIGNAL,
        )

        return self.reconstruct(
            event_id=event_id,
            descriptor=descriptor,
        )

    def reconstruct_assessment(
        self,
        *,
        event_id: UUID,
        descriptor: GovernanceACRLArtifactDescriptor,
    ) -> Mapping[str, Any]:
        self._require_type(
            descriptor,
            GovernanceACRLArtifact.RISK_ASSESSMENT,
        )

        return self.reconstruct(
            event_id=event_id,
            descriptor=descriptor,
        )

    def reconstruct_rule(
        self,
        *,
        event_id: UUID,
        descriptor: GovernanceACRLArtifactDescriptor,
    ) -> Mapping[str, Any]:
        self._require_type(
            descriptor,
            GovernanceACRLArtifact.GOVERNANCE_RULE,
        )

        return self.reconstruct(
            event_id=event_id,
            descriptor=descriptor,
        )

    def reconstruct_decision(
        self,
        *,
        event_id: UUID,
        descriptor: GovernanceACRLArtifactDescriptor,
    ) -> Mapping[str, Any]:
        self._require_type(
            descriptor,
            GovernanceACRLArtifact.GOVERNANCE_DECISION,
        )

        return self.reconstruct(
            event_id=event_id,
            descriptor=descriptor,
        )

    def reconstruct_evidence(
        self,
        *,
        event_id: UUID,
        descriptor: GovernanceACRLArtifactDescriptor,
    ) -> Mapping[str, Any]:
        self._require_type(
            descriptor,
            GovernanceACRLArtifact.GOVERNANCE_EVIDENCE,
        )

        return self.reconstruct(
            event_id=event_id,
            descriptor=descriptor,
        )

    @staticmethod
    def validate_checkpoint(
        checkpoint: GovernanceACRLCheckpoint,
        *,
        tenant_id: str,
    ) -> None:
        if not isinstance(
            checkpoint,
            GovernanceACRLCheckpoint,
        ):
            raise GovernanceACRLCheckpointError(
                "checkpoint must be GovernanceACRLCheckpoint."
            )

        if checkpoint.tenant_id != tenant_id:
            raise GovernanceACRLScopeError(
                "checkpoint tenant does not match "
                "requested tenant."
            )

    @staticmethod
    def _require_type(
        descriptor: GovernanceACRLArtifactDescriptor,
        expected: GovernanceACRLArtifact,
    ) -> None:
        if descriptor.artifact_type is not expected:
            raise GovernanceACRLError(
                f"descriptor must reference "
                f"{expected.value}."
            )


__all__ = [
    "GovernanceACRLError",
    "GovernanceACRLScopeError",
    "GovernanceACRLIntegrityError",
    "GovernanceACRLCheckpointError",
    "GovernanceACRLArtifact",
    "GovernanceACRLArtifactDescriptor",
    "GovernanceACRLCheckpoint",
    "GovernanceACRLContract",
]
