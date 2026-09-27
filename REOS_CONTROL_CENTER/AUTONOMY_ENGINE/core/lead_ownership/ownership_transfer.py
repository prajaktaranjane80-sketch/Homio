"""
CORE-003 T05 — Ownership History & Transfer

Owns:
- immutable ownership transfer record
- ownership history entries
- deterministic transfer identity
- optimistic concurrency expectation

Does NOT own:
- current ownership storage
- fraud engine
- evidence store
- authorization engine
- commission engine
- event bus
- Control Center state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID


class OwnershipTransferError(Exception):
    """Base ownership transfer error."""


class OwnershipTransferValidationError(
    OwnershipTransferError
):
    """Invalid transfer data."""


class OwnershipTransferConflictError(
    OwnershipTransferError
):
    """Transfer was based on stale ownership revision."""


class TransferReason(str, Enum):
    MANUAL = "MANUAL"
    BUSINESS_RULE = "BUSINESS_RULE"
    REASSIGNMENT = "REASSIGNMENT"
    TENANT_INTERNAL = "TENANT_INTERNAL"
    PARTNER_CHANGE = "PARTNER_CHANGE"


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise OwnershipTransferValidationError(
            f"{field_name} must be UUID"
        )

    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OwnershipTransferValidationError(
            f"{field_name} must be non-empty text"
        )

    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise OwnershipTransferValidationError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OwnershipTransferValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class OwnershipTransfer:
    transfer_id: UUID
    lead_id: UUID
    tenant_id: UUID
    previous_owner_id: UUID
    new_owner_id: UUID
    previous_revision: int
    new_revision: int
    reason: TransferReason
    transferred_at: datetime
    transfer_reference: str | None = None

    def __post_init__(self) -> None:
        _uuid(self.transfer_id, "transfer_id")
        _uuid(self.lead_id, "lead_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(
            self.previous_owner_id,
            "previous_owner_id",
        )
        _uuid(self.new_owner_id, "new_owner_id")

        if (
            self.previous_owner_id
            == self.new_owner_id
        ):
            raise OwnershipTransferValidationError(
                "Previous and new owner cannot be identical"
            )

        if not isinstance(
            self.previous_revision,
            int,
        ) or self.previous_revision < 0:
            raise OwnershipTransferValidationError(
                "previous_revision must be non-negative integer"
            )

        if not isinstance(
            self.new_revision,
            int,
        ) or self.new_revision != self.previous_revision + 1:
            raise OwnershipTransferValidationError(
                "new_revision must equal previous_revision + 1"
            )

        if not isinstance(
            self.reason,
            TransferReason,
        ):
            raise OwnershipTransferValidationError(
                "reason must be TransferReason"
            )

        object.__setattr__(
            self,
            "transferred_at",
            _time(
                self.transferred_at,
                "transferred_at",
            ),
        )

        if self.transfer_reference is not None:
            object.__setattr__(
                self,
                "transfer_reference",
                _text(
                    self.transfer_reference,
                    "transfer_reference",
                ),
            )

        @classmethod
    def create(
        cls,
        *,
        lead_id: UUID,
        tenant_id: UUID,
        previous_owner_id: UUID,
        new_owner_id: UUID,
        previous_revision: int,
        reason: TransferReason,
        transferred_at: datetime | None = None,
        transfer_id: UUID | None = None,
        transfer_reference: str | None = None,
    ) -> "OwnershipTransfer":
        from uuid import uuid4

        timestamp = (
            datetime.now(timezone.utc)
            if transferred_at is None
            else transferred_at
        )

        return cls(
            transfer_id=transfer_id or uuid4(),
            lead_id=lead_id,
            tenant_id=tenant_id,
            previous_owner_id=previous_owner_id,
            new_owner_id=new_owner_id,
            previous_revision=previous_revision,
            new_revision=previous_revision + 1,
            reason=reason,
            transferred_at=timestamp,
            transfer_reference=transfer_reference,
        )

    @property
    def history_key(self) -> tuple[UUID, UUID, int]:
        return (
            self.tenant_id,
            self.lead_id,
            self.new_revision,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "transfer_id": str(self.transfer_id),
            "lead_id": str(self.lead_id),
            "tenant_id": str(self.tenant_id),
            "previous_owner_id": str(
                self.previous_owner_id
            ),
            "new_owner_id": str(self.new_owner_id),
            "previous_revision": self.previous_revision,
            "new_revision": self.new_revision,
            "reason": self.reason.value,
            "transferred_at": self.transferred_at.isoformat(),
            "transfer_reference": self.transfer_reference,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def ensure_tenant(self, tenant_id: UUID) -> None:
        _uuid(tenant_id, "tenant_id")

        if self.tenant_id != tenant_id:
            raise OwnershipTransferValidationError(
                "Transfer belongs to another tenant"
            )

    def ensure_previous_revision(
        self,
        current_revision: int,
    ) -> None:
        if not isinstance(current_revision, int):
            raise OwnershipTransferValidationError(
                "current_revision must be integer"
            )

        if current_revision != self.previous_revision:
            raise OwnershipTransferConflictError(
                f"Stale ownership revision: expected "
                f"{self.previous_revision}, actual "
                f"{current_revision}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "transfer_id": str(self.transfer_id),
            "lead_id": str(self.lead_id),
            "tenant_id": str(self.tenant_id),
            "previous_owner_id": str(
                self.previous_owner_id
            ),
            "new_owner_id": str(self.new_owner_id),
            "previous_revision": self.previous_revision,
            "new_revision": self.new_revision,
            "reason": self.reason.value,
            "transferred_at": self.transferred_at.isoformat(),
            "transfer_reference": self.transfer_reference,
            "fingerprint": self.fingerprint,
        }
