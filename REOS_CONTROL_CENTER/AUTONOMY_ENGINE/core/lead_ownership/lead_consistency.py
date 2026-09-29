"""
CORE-003 T08 — Consistency & Concurrency

Purpose:
- Provide immutable optimistic-concurrency preconditions.
- Capture lead/ownership revisions and fingerprints.
- Detect stale state before mutation.
- Prevent silent lost-update behavior.

This module does not perform mutation or persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from uuid import UUID

from .lead import Lead
from .lead_ownership import LeadOwnership


class LeadConsistencyError(Exception):
    """Base consistency error."""


class LeadConcurrencyConflict(
    LeadConsistencyError
):
    """Current state differs from mutation precondition."""


class LeadConsistencyValidationError(
    LeadConsistencyError
):
    """Invalid consistency state."""


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise LeadConsistencyValidationError(
            f"{field_name} must be UUID"
        )
    return value


@dataclass(frozen=True, slots=True)
class LeadConsistencySnapshot:
    tenant_id: UUID
    lead_id: UUID
    lead_revision: int
    lead_fingerprint: str
    ownership_revision: int | None
    ownership_fingerprint: str | None

    @classmethod
    def capture(
        cls,
        lead: Lead,
        ownership: LeadOwnership | None,
    ) -> "LeadConsistencySnapshot":
        if not isinstance(lead, Lead):
            raise LeadConsistencyValidationError(
                "lead must be Lead"
            )

        if ownership is not None:
            if not isinstance(
                ownership,
                LeadOwnership,
            ):
                raise LeadConsistencyValidationError(
                    "ownership must be LeadOwnership or None"
                )

            if ownership.tenant_id != lead.tenant_id:
                raise LeadConsistencyValidationError(
                    "Lead and ownership tenant mismatch"
                )

            if ownership.lead_id != lead.lead_id:
                raise LeadConsistencyValidationError(
                    "Lead and ownership identity mismatch"
                )

        return cls(
            tenant_id=lead.tenant_id,
            lead_id=lead.lead_id,
            lead_revision=lead.revision,
            lead_fingerprint=lead.immutable_fingerprint,
            ownership_revision=(
                ownership.revision
                if ownership is not None
                else None
            ),
            ownership_fingerprint=(
                ownership.fingerprint
                if ownership is not None
                else None
            ),
        )

    def __post_init__(self) -> None:
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.lead_id, "lead_id")

        if not isinstance(
            self.lead_revision,
            int,
        ) or self.lead_revision < 0:
            raise LeadConsistencyValidationError(
                "lead_revision must be non-negative integer"
            )

        if not self.lead_fingerprint:
            raise LeadConsistencyValidationError(
                "lead_fingerprint is required"
            )

        if self.ownership_revision is not None:
            if (
                not isinstance(
                    self.ownership_revision,
                    int,
                )
                or self.ownership_revision < 0
            ):
                raise LeadConsistencyValidationError(
                    "ownership_revision must be non-negative integer"
                )

        if (
            self.ownership_revision is None
            and self.ownership_fingerprint is not None
        ):
            raise LeadConsistencyValidationError(
                "ownership fingerprint requires ownership revision"
            )

        if (
            self.ownership_revision is not None
            and self.ownership_fingerprint is None
        ):
            raise LeadConsistencyValidationError(
                "ownership revision requires ownership fingerprint"
            )

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "lead_revision": self.lead_revision,
            "lead_fingerprint": self.lead_fingerprint,
            "ownership_revision": self.ownership_revision,
            "ownership_fingerprint": (
                self.ownership_fingerprint
            ),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def assert_current(
        self,
        lead: Lead,
        ownership: LeadOwnership | None,
    ) -> None:
        current = type(self).capture(
            lead,
            ownership,
        )

        if current.tenant_id != self.tenant_id:
            raise LeadConcurrencyConflict(
                "Tenant changed during mutation"
            )

        if current.lead_id != self.lead_id:
            raise LeadConcurrencyConflict(
                "Lead identity changed during mutation"
            )

        if (
            current.lead_revision
            != self.lead_revision
        ):
            raise LeadConcurrencyConflict(
                "Lead revision changed during mutation"
            )

        if (
            current.lead_fingerprint
            != self.lead_fingerprint
        ):
            raise LeadConcurrencyConflict(
                "Lead immutable identity fingerprint changed"
            )

        if (
            current.ownership_revision
            != self.ownership_revision
        ):
            raise LeadConcurrencyConflict(
                "Ownership revision changed during mutation"
            )

        if (
            current.ownership_fingerprint
            != self.ownership_fingerprint
        ):
            raise LeadConcurrencyConflict(
                "Ownership fingerprint changed during mutation"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "lead_revision": self.lead_revision,
            "lead_fingerprint": self.lead_fingerprint,
            "ownership_revision": self.ownership_revision,
            "ownership_fingerprint": (
                self.ownership_fingerprint
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class LeadMutationPrecondition:
    tenant_id: UUID
    lead_id: UUID
    expected_lead_revision: int
    expected_ownership_revision: int | None
    idempotency_key: str

    def __post_init__(self) -> None:
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.lead_id, "lead_id")

        if (
            not isinstance(
                self.expected_lead_revision,
                int,
            )
            or self.expected_lead_revision < 0
        ):
            raise LeadConsistencyValidationError(
                "expected_lead_revision must be non-negative integer"
            )

        if self.expected_ownership_revision is not None:
            if (
                not isinstance(
                    self.expected_ownership_revision,
                    int,
                )
                or self.expected_ownership_revision < 0
            ):
                raise LeadConsistencyValidationError(
                    "expected_ownership_revision must be non-negative integer"
                )

        if not isinstance(
            self.idempotency_key,
            str,
        ) or not self.idempotency_key.strip():
            raise LeadConsistencyValidationError(
                "idempotency_key is required"
            )

        object.__setattr__(
            self,
            "idempotency_key",
            self.idempotency_key.strip(),
        )

    def validate_snapshot(
        self,
        snapshot: LeadConsistencySnapshot,
    ) -> None:
        if not isinstance(
            snapshot,
            LeadConsistencySnapshot,
        ):
            raise LeadConsistencyValidationError(
                "snapshot must be LeadConsistencySnapshot"
            )

        if snapshot.tenant_id != self.tenant_id:
            raise LeadConcurrencyConflict(
                "Precondition tenant mismatch"
            )

        if snapshot.lead_id != self.lead_id:
            raise LeadConcurrencyConflict(
                "Precondition lead mismatch"
            )

        if (
            snapshot.lead_revision
            != self.expected_lead_revision
        ):
            raise LeadConcurrencyConflict(
                "Lead revision does not satisfy precondition"
            )

        if (
            snapshot.ownership_revision
            != self.expected_ownership_revision
        ):
            raise LeadConcurrencyConflict(
                "Ownership revision does not satisfy precondition"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "expected_lead_revision": (
                self.expected_lead_revision
            ),
            "expected_ownership_revision": (
                self.expected_ownership_revision
            ),
            "idempotency_key": self.idempotency_key,
        }
