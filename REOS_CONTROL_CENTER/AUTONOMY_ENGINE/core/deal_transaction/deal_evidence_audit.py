from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


class DealEvidenceAuditError(ValueError):
    """Base evidence/audit integration error."""


class DealEvidenceConflictError(DealEvidenceAuditError):
    """Evidence identity was reused with different immutable data."""


class DealAuditConflictError(DealEvidenceAuditError):
    """Audit identity was reused with different immutable data."""


class DealEvidenceScopeError(DealEvidenceAuditError):
    """Evidence crosses Deal/tenant scope."""


class DealAuditScopeError(DealEvidenceAuditError):
    """Audit crosses Deal/tenant scope."""


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealEvidenceAuditError(
            f"{name} must be a non-empty string."
        )
    return value.strip()


def _timestamp(value: datetime | str | None) -> str:
    if value is None:
        dt = datetime.now(timezone.utc)
    elif isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise DealEvidenceAuditError(
                "Invalid ISO-8601 timestamp."
            ) from exc
    else:
        raise DealEvidenceAuditError(
            "Timestamp must be datetime, string, or None."
        )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc).isoformat()


def _freeze(
    mapping: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    return MappingProxyType(dict(mapping or {}))


@dataclass(frozen=True)
class DealEvidenceReference:
    """
    Immutable reference to ARCH-014 evidence.

    CORE-006 never becomes the evidence authority.
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
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name),
            )

        if (
            isinstance(self.version, bool)
            or not isinstance(self.version, int)
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
        deal_id: str,
        tenant_id: str,
        evidence_type: str,
        reference: str,
        evidence_id: str | None = None,
        version: int = 1,
        deal_version: int | None = None,
        created_at: str | None = None,
        at: datetime | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "DealEvidenceReference":
        if deal_version is not None:
            if version != 1 and version != deal_version:
                raise DealEvidenceAuditError(
                    "version and deal_version disagree."
                )
            version = deal_version

        return cls(
            evidence_id=evidence_id or str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            evidence_type=evidence_type,
            reference=reference,
            created_at=_timestamp(
                at if at is not None else created_at
            ),
            version=version,
            metadata=metadata,
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
    Immutable Deal-local audit reference.

    It does not replace the platform governance/audit authority.
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
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name),
            )

        if (
            isinstance(self.version, bool)
            or not isinstance(self.version, int)
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
        deal_id: str,
        tenant_id: str,
        action: str,
        actor_id: str,
        audit_id: str | None = None,
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

        if deal_version is not None:
            if version != 1 and version != deal_version:
                raise DealEvidenceAuditError(
                    "version and deal_version disagree."
                )
            version = deal_version

        effective_details = (
            details
            if details is not None
            else metadata
        )

        return cls(
            audit_id=audit_id or str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            action=action,
            actor_id=actor_id,
            created_at=_timestamp(
                at if at is not None else created_at
            ),
            details=effective_details,
            version=version,
            outcome=outcome,
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
