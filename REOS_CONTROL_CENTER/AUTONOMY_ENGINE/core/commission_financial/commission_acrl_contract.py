from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


CORE008_ACRL_CONTRACT_VERSION = 1
CORE008_ACRL_AUTHORITY = "AUTONOMY_ENGINE.continuity.acrl"


class CommissionACRLContractError(ValueError):
    """Base CORE-008 / ACRL integration-contract error."""


class CommissionACRLValidationError(CommissionACRLContractError):
    """Invalid CORE-008 ACRL integration data."""


class FinancialReconstructionSubject(str, Enum):
    COMMISSION = "COMMISSION"
    ENTITLEMENT = "ENTITLEMENT"
    CALCULATION = "CALCULATION"
    LEDGER = "LEDGER"
    SETTLEMENT = "SETTLEMENT"
    RECONCILIATION = "RECONCILIATION"


@dataclass(frozen=True, slots=True)
class ACRLSourceReference:
    """
    Read-only reference into an authoritative or recovery source.

    CORE-008 stores the reference.
    ACRL remains responsible for its own recovery/reconstruction engine.
    """

    source_kind: str
    source_id: str
    fingerprint: str
    authority: str = CORE008_ACRL_AUTHORITY

    def __post_init__(self) -> None:
        for name, value in (
            ("source_kind", self.source_kind),
            ("source_id", self.source_id),
            ("fingerprint", self.fingerprint),
            ("authority", self.authority),
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommissionACRLValidationError(
                    f"{name} cannot be empty"
                )

            object.__setattr__(
                self,
                name,
                value.strip(),
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "fingerprint": self.fingerprint,
            "authority": self.authority,
        }


@dataclass(frozen=True, slots=True)
class FinancialReconstructionRequest:
    """
    Immutable request describing what CORE-008 requires ACRL to reconstruct.

    The request contains references only.
    It does not perform reconstruction.
    """

    tenant_id: str
    commission_id: str
    subject: FinancialReconstructionSubject
    source_references: tuple[ACRLSourceReference, ...]
    target_fingerprint: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("tenant_id", self.tenant_id),
            ("commission_id", self.commission_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommissionACRLValidationError(
                    f"{name} cannot be empty"
                )

            object.__setattr__(
                self,
                name,
                value.strip(),
            )

        if not isinstance(
            self.subject,
            FinancialReconstructionSubject,
        ):
            raise CommissionACRLValidationError(
                "subject must be FinancialReconstructionSubject"
            )

        references = tuple(self.source_references)

        if not references:
            raise CommissionACRLValidationError(
                "at least one source reference is required"
            )

        if any(
            not isinstance(
                item,
                ACRLSourceReference,
            )
            for item in references
        ):
            raise CommissionACRLValidationError(
                "source_references contain invalid entries"
            )

        object.__setattr__(
            self,
            "source_references",
            references,
        )

        if self.target_fingerprint is not None:
            if (
                not isinstance(
                    self.target_fingerprint,
                    str,
                )
                or not self.target_fingerprint.strip()
            ):
                raise CommissionACRLValidationError(
                    "target_fingerprint cannot be empty"
                )

            object.__setattr__(
                self,
                "target_fingerprint",
                self.target_fingerprint.strip(),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "subject": self.subject.value,
            "source_references": [
                reference.to_dict()
                for reference in self.source_references
            ],
            "target_fingerprint": self.target_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ACRLCheckpointCompatibility:
    """
    Compatibility declaration for existing ACRL checkpoint/recovery services.
    """

    checkpoint_id: str
    checkpoint_fingerprint: str
    state_fingerprint: str
    schema_version: str
    authority: str = CORE008_ACRL_AUTHORITY

    def __post_init__(self) -> None:
        for name, value in (
            ("checkpoint_id", self.checkpoint_id),
            ("checkpoint_fingerprint", self.checkpoint_fingerprint),
            ("state_fingerprint", self.state_fingerprint),
            ("schema_version", self.schema_version),
            ("authority", self.authority),
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommissionACRLValidationError(
                    f"{name} cannot be empty"
                )

            object.__setattr__(
                self,
                name,
                value.strip(),
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
            "state_fingerprint": self.state_fingerprint,
            "schema_version": self.schema_version,
            "authority": self.authority,
        }


@dataclass(frozen=True, slots=True)
class CommissionACRLContract:
    """
    Canonical CORE-008 -> ACRL integration contract.

    ACRL owns:
        reconstruction
        checkpointing
        recovery
        state-integrity processing

    CORE-008 owns:
        financial references
        tenant/commission identity
        discoverability requirements
        deterministic financial reconstruction metadata

    Neither side takes ownership of the other's domain state.
    """

    contract_version: int
    tenant_id: str
    commission_id: str
    supported_subjects: tuple[FinancialReconstructionSubject, ...]
    evidence_discoverable: bool
    checkpoint_recovery_compatible: bool
    autonomous_state_mutation_allowed: bool = False
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.contract_version < 1:
            raise CommissionACRLValidationError(
                "contract_version must be >= 1"
            )

        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise CommissionACRLValidationError(
                "tenant_id cannot be empty"
            )

        if (
            not isinstance(
                self.commission_id,
                str,
            )
            or not self.commission_id.strip()
        ):
            raise CommissionACRLValidationError(
                "commission_id cannot be empty"
            )

        subjects = tuple(self.supported_subjects)

        if not subjects:
            raise CommissionACRLValidationError(
                "supported_subjects cannot be empty"
            )

        if any(
            not isinstance(
                subject,
                FinancialReconstructionSubject,
            )
            for subject in subjects
        ):
            raise CommissionACRLValidationError(
                "supported_subjects contain invalid values"
            )

        object.__setattr__(
            self,
            "supported_subjects",
            tuple(
                dict.fromkeys(subjects)
            ),
        )

        if not self.evidence_discoverable:
            raise CommissionACRLValidationError(
                "CORE-008 financial evidence must remain discoverable"
            )

        if not self.checkpoint_recovery_compatible:
            raise CommissionACRLValidationError(
                "CORE-008 must remain checkpoint/recovery compatible"
            )

        if self.autonomous_state_mutation_allowed:
            raise CommissionACRLValidationError(
                "CORE-008 ACRL contract cannot authorize autonomous state mutation"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata or {})
            ),
        )

    @classmethod
    def default(
        cls,
        *,
        tenant_id: str,
        commission_id: str,
    ) -> "CommissionACRLContract":
        return cls(
            contract_version=CORE008_ACRL_CONTRACT_VERSION,
            tenant_id=tenant_id,
            commission_id=commission_id,
            supported_subjects=tuple(
                FinancialReconstructionSubject
            ),
            evidence_discoverable=True,
            checkpoint_recovery_compatible=True,
            autonomous_state_mutation_allowed=False,
        )

    def supports(
        self,
        subject: FinancialReconstructionSubject,
    ) -> bool:
        return subject in self.supported_subjects

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "supported_subjects": [
                subject.value
                for subject in self.supported_subjects
            ],
            "evidence_discoverable": self.evidence_discoverable,
            "checkpoint_recovery_compatible": (
                self.checkpoint_recovery_compatible
            ),
            "autonomous_state_mutation_allowed": (
                self.autonomous_state_mutation_allowed
            ),
            "authority": CORE008_ACRL_AUTHORITY,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "CORE008_ACRL_AUTHORITY",
    "CORE008_ACRL_CONTRACT_VERSION",
    "CommissionACRLContract",
    "CommissionACRLContractError",
    "CommissionACRLValidationError",
    "ACRLCheckpointCompatibility",
    "ACRLSourceReference",
    "FinancialReconstructionSubject",
    "FinancialReconstructionRequest",
]
