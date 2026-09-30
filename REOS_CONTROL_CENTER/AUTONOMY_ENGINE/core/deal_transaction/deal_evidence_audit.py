from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4

from .deal_contract import (
    deep_freeze,
    deep_thaw,
    require_positive_int,
    utc_datetime,
)


class DealEvidenceAuditError(ValueError):
    pass


class DealEvidenceConflictError(DealEvidenceAuditError):
    pass


class DealAuditConflictError(DealEvidenceAuditError):
    pass


class DealEvidenceScopeError(DealEvidenceAuditError):
    pass


class DealAuditScopeError(DealEvidenceAuditError):
    pass


@dataclass(frozen=True)
class DealEvidenceReference:
    evidence_id: str
    deal_id: str
    tenant_id: str
    evidence_type: str
    reference: str
    created_at: str
    deal_version: int
    actor_id: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )
    source_of_truth: str = "ARCH-014"

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "deal_id",
            "tenant_id",
            "evidence_type",
            "reference",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise DealEvidenceAuditError(
                    f"{name} is required."
                )

        try:
            require_positive_int(
                self.deal_version,
                "deal_version",
            )
        except ValueError as exc:
            raise DealEvidenceAuditError(str(exc)) from exc

        if self.source_of_truth != "ARCH-014":
            raise DealEvidenceAuditError(
                "Evidence authority must remain ARCH-014."
            )

        object.__setattr__(
            self,
            "metadata",
            deep_freeze(self.metadata),
        )

    @classmethod
    def create(
        cls,
        *,
        deal_id: str,
        tenant_id: str,
        evidence_type: str,
        reference: str,
        deal_version: int,
        evidence_id: str | None = None,
        actor_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        at: Any = None,
    ) -> "DealEvidenceReference":
        return cls(
            evidence_id=evidence_id or str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            evidence_type=evidence_type,
            reference=reference,
            created_at=utc_datetime(at).isoformat(),
            deal_version=deal_version,
            actor_id=actor_id,
            metadata=dict(metadata or {}),
        )

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.evidence_id,
            self.deal_id,
            self.tenant_id,
            self.evidence_type,
            self.reference,
            self.actor_id,
            deep_thaw(self.metadata),
        )

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if (
            self.deal_id != deal_id
            or self.tenant_id != tenant_id
        ):
            raise DealEvidenceScopeError(
                "Evidence crosses Deal or tenant scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "evidence_type": self.evidence_type,
            "reference": self.reference,
            "created_at": self.created_at,
            "deal_version": self.deal_version,
            "actor_id": self.actor_id,
            "metadata": dict(self.metadata),
            "source_of_truth": self.source_of_truth,
        }


@dataclass(frozen=True)
class DealAuditEntry:
    audit_id: str
    deal_id: str
    tenant_id: str
    action: str
    actor_id: str
    created_at: str
    deal_version: int
    outcome: str = "RECORDED"
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )
    source_of_truth: str = "deal"

    def __post_init__(self) -> None:
        for name in (
            "audit_id",
            "deal_id",
            "tenant_id",
            "action",
            "actor_id",
            "outcome",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise DealEvidenceAuditError(
                    f"{name} is required."
                )

        try:
            require_positive_int(
                self.deal_version,
                "deal_version",
            )
        except ValueError as exc:
            raise DealEvidenceAuditError(str(exc)) from exc

        if self.source_of_truth != "deal":
            raise DealEvidenceAuditError(
                "Deal audit source_of_truth must remain 'deal'."
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @classmethod
    def create(
        cls,
        *,
        deal_id: str,
        tenant_id: str,
        action: str,
        actor_id: str,
        deal_version: int,
        audit_id: str | None = None,
        outcome: str = "RECORDED",
        metadata: Mapping[str, Any] | None = None,
        at: Any = None,
    ) -> "DealAuditEntry":
        return cls(
            audit_id=audit_id or str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            action=action,
            actor_id=actor_id,
            created_at=utc_datetime(at).isoformat(),
            deal_version=deal_version,
            outcome=outcome,
            metadata=dict(metadata or {}),
        )

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.audit_id,
            self.deal_id,
            self.tenant_id,
            self.action,
            self.actor_id,
            self.outcome,
            dict(self.metadata),
        )

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if (
            self.deal_id != deal_id
            or self.tenant_id != tenant_id
        ):
            raise DealAuditScopeError(
                "Audit entry crosses Deal or tenant scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "created_at": self.created_at,
            "deal_version": self.deal_version,
            "outcome": self.outcome,
            "metadata": dict(self.metadata),
            "source_of_truth": self.source_of_truth,
        }
