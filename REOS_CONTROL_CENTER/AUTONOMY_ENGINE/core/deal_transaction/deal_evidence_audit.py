from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


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


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealEvidenceAuditError(
            f"{name} must be a non-empty string."
        )
    return value.strip()


def _timestamp(
    value: datetime | str | None,
) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise DealEvidenceAuditError(
                "Invalid ISO-8601 timestamp."
            ) from exc

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()


def _freeze(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True)
class DealEvidenceReference:
    """
    Reference only.

    ARCH-014 remains evidence authority.
    CORE-006 stores traceability, not evidence storage.
    """

    evidence_id: str
    deal_id: str
    tenant_id: str
    evidence_type: str
    reference: str
    created_at: str
    version: int = 1
    metadata: Mapping[str, Any] = field(
        default_factory=dict,
        repr=False,
    )
    source_of_truth: str = "evidence"

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "deal_id",
            "tenant_id",
            "evidence_type",
            "reference",
        ):
            _text(getattr(self, name), name)

        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
            or self.version < 1
        ):
            raise DealEvidenceAuditError(
                "version must be an integer >= 1."
            )

        if self.source_of_truth != "evidence":
            raise DealEvidenceAuditError(
                "Evidence source_of_truth must remain 'evidence'."
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

    @classmethod
    def create(
        cls,
        *,
        evidence_id: str | None = None,
        deal_id: str,
        tenant_id: str,
        evidence_type: str,
        reference: str,
        created_at: str | None = None,
        at: datetime | str | None = None,
        version: int = 1,
        deal_version: int | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "DealEvidenceReference":
        effective_version = (
            deal_version
            if deal_version is not None
            else version
        )

        return cls(
            evidence_id or str(uuid4()),
            deal_id,
            tenant_id,
            evidence_type,
            reference,
            _timestamp(
                at if at is not None else created_at
            ),
            effective_version,
            metadata or {},
        )

    @property
    def deal_version(self) -> int:
        return self.version

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if self.deal_id != deal_id:
            raise DealEvidenceScopeError(
                "Evidence belongs to a different deal."
            )

        if self.tenant_id != tenant_id:
            raise DealEvidenceScopeError(
                "Evidence belongs to a different tenant."
            )

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.evidence_id,
            self.deal_id,
            self.tenant_id,
            self.evidence_type,
            self.reference,
            dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "evidence_type": self.evidence_type,
            "reference": self.reference,
            "created_at": self.created_at,
            "version": self.version,
            "deal_version": self.deal_version,
            "metadata": dict(self.metadata),
            "source_of_truth": self.source_of_truth,
        }


@dataclass(frozen=True)
class DealAuditEntry:
    """
    Deal-local historical reference.

    This does not replace platform governance/audit authority.
    """

    audit_id: str
    deal_id: str
    tenant_id: str
    action: str
    actor_id: str
    created_at: str
    details: Mapping[str, Any] = field(
        default_factory=dict,
        repr=False,
    )
    version: int = 1
    outcome: str = "RECORDED"
    source_of_truth: str = "deal_audit"

    def __post_init__(self) -> None:
        for name in (
            "audit_id",
            "deal_id",
            "tenant_id",
            "action",
            "actor_id",
            "outcome",
        ):
            _text(getattr(self, name), name)

        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
            or self.version < 1
        ):
            raise DealEvidenceAuditError(
                "version must be an integer >= 1."
            )

        if self.source_of_truth != "deal_audit":
            raise DealEvidenceAuditError(
                "Audit source_of_truth must remain 'deal_audit'."
            )

        object.__setattr__(
            self,
            "details",
            _freeze(self.details),
        )

    @classmethod
    def create(
        cls,
        *,
        audit_id: str | None = None,
        deal_id: str,
        tenant_id: str,
        action: str,
        actor_id: str,
        created_at: str | None = None,
        at: datetime | str | None = None,
        details: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        version: int = 1,
        deal_version: int | None = None,
        outcome: str = "RECORDED",
    ) -> "DealAuditEntry":
        if (
            details is not None
            and metadata is not None
            and dict(details) != dict(metadata)
        ):
            raise DealEvidenceAuditError(
                "details and metadata disagree."
            )

        effective_details = (
            details
            if details is not None
            else metadata
        )

        effective_version = (
            deal_version
            if deal_version is not None
            else version
        )

        return cls(
            audit_id or str(uuid4()),
            deal_id,
            tenant_id,
            action,
            actor_id,
            _timestamp(
                at if at is not None else created_at
            ),
            effective_details or {},
            effective_version,
            outcome,
        )

    @property
    def deal_version(self) -> int:
        return self.version

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self.details

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if self.deal_id != deal_id:
            raise DealAuditScopeError(
                "Audit entry belongs to a different deal."
            )

        if self.tenant_id != tenant_id:
            raise DealAuditScopeError(
                "Audit entry belongs to a different tenant."
            )

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.audit_id,
            self.deal_id,
            self.tenant_id,
            self.action,
            self.actor_id,
            self.outcome,
            dict(self.details),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "created_at": self.created_at,
            "details": dict(self.details),
            "metadata": dict(self.details),
            "version": self.version,
            "deal_version": self.deal_version,
            "outcome": self.outcome,
            "source_of_truth": self.source_of_truth,
        }


__all__ = [
    "DealAuditConflictError",
    "DealAuditEntry",
    "DealAuditScopeError",
    "DealEvidenceAuditError",
    "DealEvidenceConflictError",
    "DealEvidenceReference",
    "DealEvidenceScopeError",
]
