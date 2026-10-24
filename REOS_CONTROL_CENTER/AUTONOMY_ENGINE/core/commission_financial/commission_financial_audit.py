from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..contract_primitives import (
    ContractPrimitiveError,
    canonical_json,
    canonicalize,
    deep_freeze,
    deep_thaw,
    fingerprint,
)


CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION = 1


class CommissionFinancialAuditError(ValueError):
    """Base CORE-008 financial audit error."""


class CommissionFinancialAuditValidationError(CommissionFinancialAuditError):
    """Invalid immutable financial audit record."""


class CommissionFinancialAuditConflictError(CommissionFinancialAuditError):
    """Conflicting replay or mutation of an existing audit identity."""


class CommissionFinancialAuditIntegrityError(CommissionFinancialAuditError):
    """Audit chain integrity could not be verified."""


class CommissionFinancialAuditAction(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"
    RECONCILED = "RECONCILED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"
    REVERSED = "REVERSED"
    RELEASED = "RELEASED"
    EVIDENCE_LINKED = "EVIDENCE_LINKED"
    REPORT_EXPORTED = "REPORT_EXPORTED"


class CommissionFinancialAuditOutcome(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


_CRITICAL_AUTHORIZATION_ACTIONS = frozenset({
    CommissionFinancialAuditAction.APPROVED,
    CommissionFinancialAuditAction.SETTLED,
    CommissionFinancialAuditAction.RECONCILED,
    CommissionFinancialAuditAction.RESOLVED,
    CommissionFinancialAuditAction.REVERSED,
    CommissionFinancialAuditAction.RELEASED,
})

_EVIDENCE_REQUIRED_ACTIONS = frozenset({
    CommissionFinancialAuditAction.SETTLED,
    CommissionFinancialAuditAction.RECONCILED,
    CommissionFinancialAuditAction.RESOLVED,
    CommissionFinancialAuditAction.REVERSED,
})

_STATE_CHANGE_ACTIONS = frozenset({
    CommissionFinancialAuditAction.CREATED,
    CommissionFinancialAuditAction.UPDATED,
    CommissionFinancialAuditAction.SETTLED,
    CommissionFinancialAuditAction.RECONCILED,
    CommissionFinancialAuditAction.DISPUTED,
    CommissionFinancialAuditAction.RESOLVED,
    CommissionFinancialAuditAction.REVERSED,
    CommissionFinancialAuditAction.RELEASED,
})


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionFinancialAuditValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _optional_text(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field)


def _aware_utc(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionFinancialAuditValidationError(
            f"{field} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class CommissionFinancialEvidenceLink:
    """A pointer to externally governed evidence; this object stores no evidence bytes."""

    evidence_kind: str
    evidence_id: str
    evidence_fingerprint: str
    authority_reference: str

    def __post_init__(self) -> None:
        for field in (
            "evidence_kind",
            "evidence_id",
            "evidence_fingerprint",
            "authority_reference",
        ):
            object.__setattr__(
                self,
                field,
                _required_text(getattr(self, field), field),
            )

    @property
    def identity_key(self) -> tuple[str, str]:
        return self.evidence_kind, self.evidence_id

    def to_dict(self) -> dict[str, str]:
        return {
            "evidence_kind": self.evidence_kind,
            "evidence_id": self.evidence_id,
            "evidence_fingerprint": self.evidence_fingerprint,
            "authority_reference": self.authority_reference,
        }


@dataclass(frozen=True, slots=True)
class CommissionFinancialAuditEntry:
    """Immutable tenant-scoped audit fact for a financial subject."""

    audit_id: str
    tenant_id: str
    commission_id: str
    subject_type: str
    subject_id: str
    subject_version: int
    action: CommissionFinancialAuditAction
    outcome: CommissionFinancialAuditOutcome
    actor_reference: str
    occurred_at: datetime
    subject_fingerprint: str
    provenance_reference: str
    authorization_reference: str | None = None
    before_fingerprint: str | None = None
    after_fingerprint: str | None = None
    evidence_links: tuple[CommissionFinancialEvidenceLink, ...] = ()
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "audit_id",
            "tenant_id",
            "commission_id",
            "subject_type",
            "subject_id",
            "actor_reference",
            "subject_fingerprint",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                field,
                _required_text(getattr(self, field), field),
            )

        if (
            isinstance(self.subject_version, bool)
            or not isinstance(self.subject_version, int)
            or self.subject_version < 1
        ):
            raise CommissionFinancialAuditValidationError(
                "subject_version must be a positive integer."
            )

        try:
            action = CommissionFinancialAuditAction(self.action)
            outcome = CommissionFinancialAuditOutcome(self.outcome)
        except (TypeError, ValueError) as exc:
            raise CommissionFinancialAuditValidationError(
                "Unsupported financial audit action or outcome."
            ) from exc

        object.__setattr__(self, "action", action)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(
            self,
            "occurred_at",
            _aware_utc(self.occurred_at, "occurred_at"),
        )
        object.__setattr__(
            self,
            "authorization_reference",
            _optional_text(self.authorization_reference, "authorization_reference"),
        )
        object.__setattr__(
            self,
            "before_fingerprint",
            _optional_text(self.before_fingerprint, "before_fingerprint"),
        )
        object.__setattr__(
            self,
            "after_fingerprint",
            _optional_text(self.after_fingerprint, "after_fingerprint"),
        )

        try:
            links = tuple(self.evidence_links)
        except TypeError as exc:
            raise CommissionFinancialAuditValidationError(
                "evidence_links must be an iterable of evidence references."
            ) from exc

        if (
            action in _CRITICAL_AUTHORIZATION_ACTIONS
            and outcome is CommissionFinancialAuditOutcome.SUCCEEDED
            and self.authorization_reference is None
        ):
            raise CommissionFinancialAuditValidationError(
                f"Successful {action.value} audit entries require authorization_reference."
            )

        if (
            action in _EVIDENCE_REQUIRED_ACTIONS
            and outcome is CommissionFinancialAuditOutcome.SUCCEEDED
            and not links
        ):
            raise CommissionFinancialAuditValidationError(
                f"Successful {action.value} audit entries require evidence links."
            )

        if (
            action in _STATE_CHANGE_ACTIONS
            and outcome is CommissionFinancialAuditOutcome.SUCCEEDED
            and self.after_fingerprint is None
        ):
            raise CommissionFinancialAuditValidationError(
                f"Successful {action.value} audit entries require after_fingerprint."
            )

        if (
            action is CommissionFinancialAuditAction.CREATED
            and self.before_fingerprint is not None
        ):
            raise CommissionFinancialAuditValidationError(
                "CREATED audit entries cannot have before_fingerprint."
            )

        seen: set[tuple[str, str]] = set()
        for link in links:
            if not isinstance(link, CommissionFinancialEvidenceLink):
                raise CommissionFinancialAuditValidationError(
                    "evidence_links must contain CommissionFinancialEvidenceLink entries."
                )
            if link.identity_key in seen:
                raise CommissionFinancialAuditValidationError(
                    "Duplicate evidence link identity."
                )
            seen.add(link.identity_key)
        object.__setattr__(self, "evidence_links", links)

        metadata = {} if self.metadata == () else self.metadata
        if not isinstance(metadata, Mapping):
            raise CommissionFinancialAuditValidationError(
                "metadata must be a mapping."
            )
        try:
            frozen = deep_freeze(dict(metadata), field_name="metadata")
            # Reject nondeterministic JSON values such as NaN and infinity.
            canonical_json(deep_thaw(frozen))
        except (ContractPrimitiveError, TypeError, ValueError) as exc:
            raise CommissionFinancialAuditValidationError(
                "metadata must contain supported deterministic values."
            ) from exc
        object.__setattr__(self, "metadata", frozen)

    @property
    def identity_key(self) -> tuple[str, str, str]:
        return self.tenant_id, self.commission_id, self.audit_id

    @property
    def immutable_fingerprint(self) -> str:
        return fingerprint(self.to_dict(include_fingerprint=False))

    def assert_tenant(self, tenant_id: str) -> None:
        expected = _required_text(tenant_id, "tenant_id")
        if expected != self.tenant_id:
            raise CommissionFinancialAuditValidationError(
                "Financial audit entry crossed tenant scope."
            )

    def to_dict(self, *, include_fingerprint: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION,
            "audit_id": self.audit_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "subject_version": self.subject_version,
            "action": self.action.value,
            "outcome": self.outcome.value,
            "actor_reference": self.actor_reference,
            "occurred_at": self.occurred_at.isoformat(),
            "subject_fingerprint": self.subject_fingerprint,
            "provenance_reference": self.provenance_reference,
            "authorization_reference": self.authorization_reference,
            "before_fingerprint": self.before_fingerprint,
            "after_fingerprint": self.after_fingerprint,
            "evidence_links": [link.to_dict() for link in self.evidence_links],
            "metadata": canonicalize(deep_thaw(self.metadata)),
        }
        if include_fingerprint:
            result["immutable_fingerprint"] = self.immutable_fingerprint
        return result


@dataclass(frozen=True, slots=True)
class CommissionFinancialAuditRecord:
    """One audit entry sealed into an append-only fingerprint chain."""

    sequence: int
    entry: CommissionFinancialAuditEntry
    previous_record_fingerprint: str | None
    record_fingerprint: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 1
        ):
            raise CommissionFinancialAuditValidationError(
                "audit record sequence must be a positive integer."
            )
        if not isinstance(self.entry, CommissionFinancialAuditEntry):
            raise CommissionFinancialAuditValidationError(
                "entry must be CommissionFinancialAuditEntry."
            )
        object.__setattr__(
            self,
            "previous_record_fingerprint",
            _optional_text(self.previous_record_fingerprint, "previous_record_fingerprint"),
        )
        object.__setattr__(
            self,
            "record_fingerprint",
            _required_text(self.record_fingerprint, "record_fingerprint"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "entry": self.entry.to_dict(),
            "previous_record_fingerprint": self.previous_record_fingerprint,
            "record_fingerprint": self.record_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class CommissionFinancialAuditIntegrityReport:
    valid: bool
    tenant_id: str
    commission_id: str
    entry_count: int
    chain_fingerprint: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "entry_count": self.entry_count,
            "chain_fingerprint": self.chain_fingerprint,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class CommissionFinancialAuditTrail:
    """Immutable append-only audit chain, scoped to one tenant and commission."""

    tenant_id: str
    commission_id: str
    records: tuple[CommissionFinancialAuditRecord, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenant_id", _required_text(self.tenant_id, "tenant_id"))
        object.__setattr__(self, "commission_id", _required_text(self.commission_id, "commission_id"))
        records = tuple(self.records)
        if any(not isinstance(item, CommissionFinancialAuditRecord) for item in records):
            raise CommissionFinancialAuditValidationError(
                "records must contain CommissionFinancialAuditRecord entries."
            )
        object.__setattr__(self, "records", records)

    @property
    def chain_fingerprint(self) -> str:
        if self.records:
            return self.records[-1].record_fingerprint
        return fingerprint({
            "schema_version": CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "records": [],
        })

    @property
    def latest(self) -> CommissionFinancialAuditRecord | None:
        return self.records[-1] if self.records else None

    def append(self, entry: CommissionFinancialAuditEntry) -> "CommissionFinancialAuditTrail":
        report = inspect_financial_audit_trail(self)
        if not report.valid:
            raise CommissionFinancialAuditIntegrityError(
                "Cannot append to an invalid audit trail: " + report.reason
            )
        if not isinstance(entry, CommissionFinancialAuditEntry):
            raise CommissionFinancialAuditValidationError(
                "entry must be CommissionFinancialAuditEntry."
            )
        if entry.tenant_id != self.tenant_id or entry.commission_id != self.commission_id:
            raise CommissionFinancialAuditValidationError(
                "Financial audit entry does not match trail tenant/commission scope."
            )

        for existing in self.records:
            if existing.entry.audit_id == entry.audit_id:
                if existing.entry.immutable_fingerprint == entry.immutable_fingerprint:
                    return self
                raise CommissionFinancialAuditConflictError(
                    "Audit ID replay conflicts with existing immutable content."
                )

        if self.latest is not None and entry.occurred_at < self.latest.entry.occurred_at:
            raise CommissionFinancialAuditValidationError(
                "Audit entries must be appended in nondecreasing occurred_at order."
            )

        sequence = 1 if self.latest is None else self.latest.sequence + 1
        previous = None if self.latest is None else self.latest.record_fingerprint
        record_fingerprint = fingerprint({
            "schema_version": CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION,
            "sequence": sequence,
            "entry_fingerprint": entry.immutable_fingerprint,
            "previous_record_fingerprint": previous,
        })
        record = CommissionFinancialAuditRecord(
            sequence=sequence,
            entry=entry,
            previous_record_fingerprint=previous,
            record_fingerprint=record_fingerprint,
        )
        return CommissionFinancialAuditTrail(
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            records=self.records + (record,),
        )

    def find(self, audit_id: str) -> CommissionFinancialAuditRecord | None:
        audit_id = _required_text(audit_id, "audit_id")
        return next(
            (record for record in self.records if record.entry.audit_id == audit_id),
            None,
        )

    def verify_integrity(self) -> bool:
        return inspect_financial_audit_trail(self).valid

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "entry_count": len(self.records),
            "chain_fingerprint": self.chain_fingerprint,
            "records": [record.to_dict() for record in self.records],
        }


def inspect_financial_audit_trail(
    trail: CommissionFinancialAuditTrail,
) -> CommissionFinancialAuditIntegrityReport:
    if not isinstance(trail, CommissionFinancialAuditTrail):
        return CommissionFinancialAuditIntegrityReport(
            valid=False,
            tenant_id="",
            commission_id="",
            entry_count=0,
            chain_fingerprint="",
            reason="trail must be CommissionFinancialAuditTrail.",
        )

    seen: dict[str, str] = {}
    expected_previous: str | None = None
    previous_time: datetime | None = None

    for expected_sequence, record in enumerate(trail.records, start=1):
        if not isinstance(record, CommissionFinancialAuditRecord):
            return CommissionFinancialAuditIntegrityReport(
                False, trail.tenant_id, trail.commission_id, len(trail.records),
                trail.chain_fingerprint, "audit chain contains an invalid record type."
            )
        if record.sequence != expected_sequence:
            return CommissionFinancialAuditIntegrityReport(
                False, trail.tenant_id, trail.commission_id, len(trail.records),
                trail.chain_fingerprint,
                f"audit sequence gap: expected {expected_sequence}, got {record.sequence}.",
            )
        entry = record.entry
        if entry.tenant_id != trail.tenant_id or entry.commission_id != trail.commission_id:
            return CommissionFinancialAuditIntegrityReport(
                False, trail.tenant_id, trail.commission_id, len(trail.records),
                trail.chain_fingerprint, "audit record crossed tenant or commission scope."
            )
        if record.previous_record_fingerprint != expected_previous:
            return CommissionFinancialAuditIntegrityReport(
                False, trail.tenant_id, trail.commission_id, len(trail.records),
                trail.chain_fingerprint, "audit previous-record fingerprint link is invalid."
            )
        expected_record_fingerprint = fingerprint({
            "schema_version": CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION,
            "sequence": expected_sequence,
            "entry_fingerprint": entry.immutable_fingerprint,
            "previous_record_fingerprint": expected_previous,
        })
        if record.record_fingerprint != expected_record_fingerprint:
            return CommissionFinancialAuditIntegrityReport(
                False, trail.tenant_id, trail.commission_id, len(trail.records),
                trail.chain_fingerprint, "audit record fingerprint is invalid."
            )
        if previous_time is not None and entry.occurred_at < previous_time:
            return CommissionFinancialAuditIntegrityReport(
                False, trail.tenant_id, trail.commission_id, len(trail.records),
                trail.chain_fingerprint, "audit event timestamps are not ordered."
            )
        prior = seen.get(entry.audit_id)
        if prior is not None:
            reason = (
                "duplicate audit ID contains conflicting content."
                if prior != entry.immutable_fingerprint
                else "duplicate audit ID appears more than once in the chain."
            )
            return CommissionFinancialAuditIntegrityReport(
                False, trail.tenant_id, trail.commission_id, len(trail.records),
                trail.chain_fingerprint, reason
            )
        seen[entry.audit_id] = entry.immutable_fingerprint
        expected_previous = record.record_fingerprint
        previous_time = entry.occurred_at

    return CommissionFinancialAuditIntegrityReport(
        valid=True,
        tenant_id=trail.tenant_id,
        commission_id=trail.commission_id,
        entry_count=len(trail.records),
        chain_fingerprint=trail.chain_fingerprint,
    )


def assert_financial_audit_trail_integrity(
    trail: CommissionFinancialAuditTrail,
) -> None:
    report = inspect_financial_audit_trail(trail)
    if not report.valid:
        raise CommissionFinancialAuditIntegrityError(report.reason)


__all__ = [
    "CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION",
    "CommissionFinancialAuditError",
    "CommissionFinancialAuditValidationError",
    "CommissionFinancialAuditConflictError",
    "CommissionFinancialAuditIntegrityError",
    "CommissionFinancialAuditAction",
    "CommissionFinancialAuditOutcome",
    "CommissionFinancialEvidenceLink",
    "CommissionFinancialAuditEntry",
    "CommissionFinancialAuditRecord",
    "CommissionFinancialAuditIntegrityReport",
    "CommissionFinancialAuditTrail",
    "inspect_financial_audit_trail",
    "assert_financial_audit_trail_integrity",
]
