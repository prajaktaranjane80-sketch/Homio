from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping

from .commission_entitlement import CommissionEntitlement


CORE008_COMMISSION_PROTECTION_SCHEMA_VERSION = 1


class CommissionProtectionError(ValueError):
    """Base commission-protection error."""


class CommissionProtectionValidationError(
    CommissionProtectionError
):
    """Invalid commission-protection state."""


class CommissionProtectionState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PROTECTED = "PROTECTED"
    FROZEN = "FROZEN"
    DISPUTED = "DISPUTED"
    RELEASED = "RELEASED"
    VOID = "VOID"


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionProtectionValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionProtectionValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class ProtectionEvidenceReference:
    evidence_type: str
    evidence_id: str
    fingerprint: str
    source_reference: str

    def __post_init__(self) -> None:
        for field in (
            "evidence_type",
            "evidence_id",
            "fingerprint",
            "source_reference",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "evidence_type": self.evidence_type,
            "evidence_id": self.evidence_id,
            "fingerprint": self.fingerprint,
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True, slots=True)
class CommissionProtection:
    """
    Immutable financial-protection record.

    CORE-008 stores protection evidence and financial linkage.

    It does NOT own:
    - lead ownership
    - customer ownership
    - attribution engine
    - fraud engine
    - governance engine
    - authorization engine
    - dispute engine
    """

    protection_id: str
    tenant_id: str
    commission_id: str
    entitlement_id: str

    lead_reference: str
    deal_reference: str
    ownership_reference: str

    attribution_evidence: tuple[
        ProtectionEvidenceReference, ...
    ]
    entitlement_evidence: tuple[
        ProtectionEvidenceReference, ...
    ]

    dispute_reference: str | None

    protection_version: int
    state: CommissionProtectionState

    captured_at: datetime
    provenance_reference: str

    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "protection_id",
            "tenant_id",
            "commission_id",
            "entitlement_id",
            "lead_reference",
            "deal_reference",
            "ownership_reference",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        if (
            isinstance(self.protection_version, bool)
            or not isinstance(
                self.protection_version,
                int,
            )
            or self.protection_version < 1
        ):
            raise CommissionProtectionValidationError(
                "protection_version must be a positive integer."
            )

        try:
            state = CommissionProtectionState(
                self.state
            )
        except ValueError as exc:
            raise CommissionProtectionValidationError(
                "Unsupported protection state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        attribution = tuple(
            self.attribution_evidence
        )
        entitlement = tuple(
            self.entitlement_evidence
        )

        if not attribution:
            raise CommissionProtectionValidationError(
                "attribution_evidence is required."
            )

        if not entitlement:
            raise CommissionProtectionValidationError(
                "entitlement_evidence is required."
            )

        for reference in (
            attribution + entitlement
        ):
            if not isinstance(
                reference,
                ProtectionEvidenceReference,
            ):
                raise CommissionProtectionValidationError(
                    "invalid protection evidence reference."
                )

        object.__setattr__(
            self,
            "attribution_evidence",
            attribution,
        )
        object.__setattr__(
            self,
            "entitlement_evidence",
            entitlement,
        )

        if self.dispute_reference is not None:
            object.__setattr__(
                self,
                "dispute_reference",
                _text(
                    self.dispute_reference,
                    "dispute_reference",
                ),
            )

        if (
            state is CommissionProtectionState.DISPUTED
            and not self.dispute_reference
        ):
            raise CommissionProtectionValidationError(
                "DISPUTED protection requires dispute_reference."
            )

        object.__setattr__(
            self,
            "captured_at",
            _aware(
                self.captured_at,
                "captured_at",
            ),
        )

        metadata = (
            {}
            if self.metadata == ()
            else self.metadata
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise CommissionProtectionValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(metadata)),
        )

    @classmethod
    def from_entitlement(
        cls,
        entitlement: CommissionEntitlement,
        *,
        protection_id: str,
        lead_reference: str,
        deal_reference: str,
        ownership_reference: str,
        attribution_evidence: tuple[
            ProtectionEvidenceReference, ...
        ],
        entitlement_evidence: tuple[
            ProtectionEvidenceReference, ...
        ],
        provenance_reference: str,
        captured_at: datetime,
        dispute_reference: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionProtection":
        if not isinstance(
            entitlement,
            CommissionEntitlement,
        ):
            raise CommissionProtectionValidationError(
                "entitlement must be CommissionEntitlement."
            )

        return cls(
            protection_id=protection_id,
            tenant_id=entitlement.tenant_id,
            commission_id=entitlement.commission_id,
            entitlement_id=entitlement.entitlement_id,
            lead_reference=lead_reference,
            deal_reference=deal_reference,
            ownership_reference=ownership_reference,
            attribution_evidence=attribution_evidence,
            entitlement_evidence=entitlement_evidence,
            dispute_reference=dispute_reference,
            protection_version=1,
            state=(
                CommissionProtectionState.DISPUTED
                if dispute_reference
                else CommissionProtectionState.PROTECTED
            ),
            captured_at=captured_at,
            provenance_reference=provenance_reference,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str, int]:
        return (
            self.tenant_id,
            self.protection_id,
            self.protection_version,
        )

    @property
    def immutable_fingerprint(self) -> str:
        payload = self.to_dict(
            include_fingerprint=False
        )

        return sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise CommissionProtectionError(
                "Commission protection crossed tenant boundary."
            )

    def with_state(
        self,
        state: CommissionProtectionState,
        *,
        dispute_reference: str | None = None,
    ) -> "CommissionProtection":
        return CommissionProtection(
            protection_id=self.protection_id,
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            entitlement_id=self.entitlement_id,
            lead_reference=self.lead_reference,
            deal_reference=self.deal_reference,
            ownership_reference=self.ownership_reference,
            attribution_evidence=self.attribution_evidence,
            entitlement_evidence=self.entitlement_evidence,
            dispute_reference=(
                dispute_reference
                if dispute_reference is not None
                else self.dispute_reference
            ),
            protection_version=(
                self.protection_version + 1
            ),
            state=state,
            captured_at=self.captured_at,
            provenance_reference=self.provenance_reference,
            metadata=self.metadata,
        )

    def verify_integrity(self) -> bool:
        return bool(
            self.immutable_fingerprint
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_PROTECTION"
            ),
            "schema_version": (
                CORE008_COMMISSION_PROTECTION_SCHEMA_VERSION
            ),
            "protection_id": self.protection_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "entitlement_id": self.entitlement_id,
            "lead_reference": self.lead_reference,
            "deal_reference": self.deal_reference,
            "ownership_reference": self.ownership_reference,
            "attribution_evidence": [
                item.to_dict()
                for item in self.attribution_evidence
            ],
            "entitlement_evidence": [
                item.to_dict()
                for item in self.entitlement_evidence
            ],
            "dispute_reference": self.dispute_reference,
            "protection_version": self.protection_version,
            "state": self.state.value,
            "captured_at": self.captured_at.isoformat(),
            "provenance_reference": (
                self.provenance_reference
            ),
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_PROTECTION_SCHEMA_VERSION",
    "CommissionProtection",
    "CommissionProtectionError",
    "CommissionProtectionState",
    "CommissionProtectionValidationError",
    "ProtectionEvidenceReference",
]
