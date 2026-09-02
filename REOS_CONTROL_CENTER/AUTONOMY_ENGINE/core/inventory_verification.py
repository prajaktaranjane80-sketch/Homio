"""Authoritative REOS inventory verification capability for CORE-004-T05.

T05 owns verification workflow and verification state.

The canonical Inventory aggregate remains authoritative for:
    - inventory identity
    - tenant/project scope
    - inventory type
    - lifecycle
    - availability
    - version

This module does NOT duplicate or mutate canonical Inventory state.

Verification is represented as a persistence-neutral capability result
linked to the canonical inventory identity/version.

History/evidence persistence, indexing, consistency, and concurrency
orchestration remain owned by their dedicated CORE-004 subtasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from .inventory import (
    Inventory,
    InventoryProjectViolation,
    InventoryTenantViolation,
)


class InventoryVerificationError(ValueError):
    """Base error for inventory verification failures."""


class InventoryVerificationState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class InventoryVerificationTransitionError(InventoryVerificationError):
    """Raised when a verification state transition is invalid."""


class InventoryVerificationRequirementError(InventoryVerificationError):
    """Raised when verification requirements are incomplete."""


_ALLOWED_VERIFICATION_TRANSITIONS: dict[
    InventoryVerificationState,
    frozenset[InventoryVerificationState],
] = {
    InventoryVerificationState.UNVERIFIED: frozenset(
        {
            InventoryVerificationState.PENDING,
        }
    ),
    InventoryVerificationState.PENDING: frozenset(
        {
            InventoryVerificationState.VERIFIED,
            InventoryVerificationState.REJECTED,
        }
    ),
    InventoryVerificationState.VERIFIED: frozenset(
        {
            InventoryVerificationState.PENDING,
        }
    ),
    InventoryVerificationState.REJECTED: frozenset(
        {
            InventoryVerificationState.PENDING,
        }
    ),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class InventoryVerificationEvent:
    """Persistence-neutral verification domain event."""

    event_id: str
    event_type: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_version: int
    verification_state: InventoryVerificationState
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_version": self.inventory_version,
            "verification_state": self.verification_state.value,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class InventoryVerification:
    """Immutable verification state linked to canonical Inventory."""

    verification_id: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_version: int
    state: InventoryVerificationState
    verified_by: str | None
    reason: str | None
    created_at: str
    updated_at: str
    version: int = 1

    @classmethod
    def for_inventory(
        cls,
        inventory: Inventory,
        *,
        at: str | None = None,
        verification_id: str | None = None,
    ) -> "InventoryVerification":
        timestamp = at or _utc_now()

        return cls(
            verification_id=verification_id or str(uuid4()),
            inventory_id=inventory.inventory_id,
            tenant_id=inventory.tenant_id,
            project_id=inventory.project_id,
            inventory_version=inventory.version,
            state=InventoryVerificationState.UNVERIFIED,
            verified_by=None,
            reason=None,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def assert_inventory_scope(
        self,
        inventory: Inventory,
        *,
        tenant_id: str,
        project_id: str,
    ) -> None:
        try:
            inventory.assert_tenant(tenant_id)
            inventory.assert_project(project_id)
        except (
            InventoryTenantViolation,
            InventoryProjectViolation,
        ) as exc:
            raise InventoryVerificationError(str(exc)) from exc

        if self.inventory_id != inventory.inventory_id:
            raise InventoryVerificationError(
                "Verification does not belong to the supplied inventory."
            )

        if self.tenant_id != inventory.tenant_id:
            raise InventoryVerificationError(
                "Verification belongs to a different tenant."
            )

        if self.project_id != inventory.project_id:
            raise InventoryVerificationError(
                "Verification belongs to a different project."
            )

        if self.inventory_version != inventory.version:
            raise InventoryVerificationError(
                "Verification is stale for the supplied inventory version."
            )


    def transition(
        self,
        inventory: Inventory,
        target: InventoryVerificationState,
        *,
        tenant_id: str,
        project_id: str,
        verified_by: str | None = None,
        reason: str | None = None,
        at: str | None = None,
    ) -> tuple["InventoryVerification", InventoryVerificationEvent]:
        """Apply one deterministic verification transition."""

        self.assert_inventory_scope(
            inventory,
            tenant_id=tenant_id,
            project_id=project_id,
        )

        target = InventoryVerificationState(target)

        if target not in _ALLOWED_VERIFICATION_TRANSITIONS[self.state]:
            raise InventoryVerificationTransitionError(
                "Invalid inventory verification transition: "
                f"{self.state.value} -> {target.value}."
            )

        if target is InventoryVerificationState.VERIFIED:
            if not verified_by or not verified_by.strip():
                raise InventoryVerificationRequirementError(
                    "verified_by is required when verification is accepted."
                )

        if target is InventoryVerificationState.REJECTED:
            if not reason or not reason.strip():
                raise InventoryVerificationRequirementError(
                    "reason is required when verification is rejected."
                )

        timestamp = at or _utc_now()

        updated = InventoryVerification(
            verification_id=self.verification_id,
            inventory_id=self.inventory_id,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            inventory_version=self.inventory_version,
            state=target,
            verified_by=(
                verified_by.strip()
                if target is InventoryVerificationState.VERIFIED
                else None
            ),
            reason=(
                reason.strip()
                if target is InventoryVerificationState.REJECTED
                else None
            ),
            created_at=self.created_at,
            updated_at=timestamp,
            version=self.version + 1,
        )

        event = InventoryVerificationEvent(
            event_id=str(uuid4()),
            event_type="INVENTORY_VERIFICATION_CHANGED",
            inventory_id=self.inventory_id,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            inventory_version=self.inventory_version,
            verification_state=target,
            occurred_at=timestamp,
            payload={
                "from": self.state.value,
                "to": target.value,
                "verification_id": self.verification_id,
                "verification_version": updated.version,
            },
        )

        return updated, event

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_version": self.inventory_version,
            "state": self.state.value,
            "verified_by": self.verified_by,
            "reason": self.reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }


__all__ = [
    "InventoryVerification",
    "InventoryVerificationError",
    "InventoryVerificationEvent",
    "InventoryVerificationRequirementError",
    "InventoryVerificationState",
    "InventoryVerificationTransitionError",
]