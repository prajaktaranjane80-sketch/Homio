"""
CORE-004 T05 — Availability & Inventory State

Owns:
- availability state
- inventory availability status
- reservation boundary
- allocation boundary
- stale-state protection
- compare-and-swap style availability updates
- state version
- deterministic availability transitions

Does NOT own:
- lifecycle transition graph
- provenance
- commercial attributes
- persistence
- authorization
- event transport
- idempotency storage
- duplicate-command registry
- REOS Control Center state
- ACRL execution

Part 08 owns broader aggregate consistency, duplicate command handling
and cross-command idempotency. This module provides the availability-level
preconditions required by that layer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .inventory import (
    AvailabilityState,
    Inventory,
)


class InventoryAvailabilityError(ValueError):
    """Base CORE-004 availability error."""


class InvalidAvailabilityTransition(
    InventoryAvailabilityError
):
    """Raised when an availability transition is invalid."""


class AvailabilityVersionConflict(
    InventoryAvailabilityError
):
    """Raised when an availability mutation uses stale state."""


class ReservationBoundaryError(
    InventoryAvailabilityError
):
    """Raised when reservation rules are violated."""


class AllocationBoundaryError(
    InventoryAvailabilityError
):
    """Raised when allocation rules are violated."""


class AvailabilityTenantViolation(
    InventoryAvailabilityError
):
    """Raised when availability mutation crosses tenants."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware_time(
    value: datetime,
    name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise InventoryAvailabilityError(
            f"{name} must be datetime."
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise InventoryAvailabilityError(
            f"{name} must be timezone-aware."
        )

    return value.astimezone(
        timezone.utc
    )


def _text(
    value: str | None,
    name: str,
) -> str | None:
    if value is None:
        return None

    if not isinstance(
        value,
        str,
    ):
        raise InventoryAvailabilityError(
            f"{name} must be string."
        )

    value = value.strip()

    if not value:
        raise InventoryAvailabilityError(
            f"{name} cannot be empty."
        )

    return value


# ---------------------------------------------------------------------------
# Availability transition graph
# ---------------------------------------------------------------------------


AVAILABILITY_TRANSITIONS: Mapping[
    AvailabilityState,
    frozenset[AvailabilityState],
] = {
    AvailabilityState.AVAILABLE: frozenset(
        {
            AvailabilityState.RESERVED,
            AvailabilityState.BLOCKED,
            AvailabilityState.UNAVAILABLE,
        }
    ),
    AvailabilityState.RESERVED: frozenset(
        {
            AvailabilityState.AVAILABLE,
            AvailabilityState.ALLOCATED,
            AvailabilityState.BLOCKED,
            AvailabilityState.UNAVAILABLE,
        }
    ),
    AvailabilityState.ALLOCATED: frozenset(
        {
            AvailabilityState.RESERVED,
            AvailabilityState.SOLD,
            AvailabilityState.BLOCKED,
            AvailabilityState.UNAVAILABLE,
        }
    ),
    AvailabilityState.BLOCKED: frozenset(
        {
            AvailabilityState.AVAILABLE,
            AvailabilityState.UNAVAILABLE,
        }
    ),
    AvailabilityState.SOLD: frozenset(),
    AvailabilityState.UNAVAILABLE: frozenset(
        {
            AvailabilityState.AVAILABLE,
            AvailabilityState.BLOCKED,
        }
    ),
}


@dataclass(frozen=True, slots=True)
class AvailabilityTransition:
    """
    Immutable availability state mutation record.

    The record describes one compare-and-swap style mutation.
    """

    transition_id: str
    tenant_id: str
    inventory_id: str
    from_state: AvailabilityState
    to_state: AvailabilityState
    from_version: int
    to_version: int
    occurred_at: datetime
    reservation_reference: str | None = None
    allocation_reference: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.transition_id,
            str,
        ) or not self.transition_id.strip():
            raise InventoryAvailabilityError(
                "transition_id is required."
            )

        if not isinstance(
            self.tenant_id,
            str,
        ) or not self.tenant_id.strip():
            raise InventoryAvailabilityError(
                "tenant_id is required."
            )

        if not isinstance(
            self.inventory_id,
            str,
        ) or not self.inventory_id.strip():
            raise InventoryAvailabilityError(
                "inventory_id is required."
            )

        try:
            from_state = AvailabilityState(
                self.from_state
            )
            to_state = AvailabilityState(
                self.to_state
            )
        except (TypeError, ValueError) as exc:
            raise InventoryAvailabilityError(
                "Invalid availability state."
            ) from exc

        object.__setattr__(
            self,
            "from_state",
            from_state,
        )

        object.__setattr__(
            self,
            "to_state",
            to_state,
        )

        if (
            not isinstance(
                self.from_version,
                int,
            )
            or self.from_version < 1
        ):
            raise InventoryAvailabilityError(
                "from_version must be >= 1."
            )

        if (
            not isinstance(
                self.to_version,
                int,
            )
            or self.to_version
            != self.from_version + 1
        ):
            raise InventoryAvailabilityError(
                "Availability mutation must increment "
                "version exactly once."
            )

        object.__setattr__(
            self,
            "occurred_at",
            _aware_time(
                self.occurred_at,
                "occurred_at",
            ),
        )

        object.__setattr__(
            self,
            "reservation_reference",
            _text(
                self.reservation_reference,
                "reservation_reference",
            ),
        )

        object.__setattr__(
            self,
            "allocation_reference",
            _text(
                self.allocation_reference,
                "allocation_reference",
            ),
        )

    @property
    def mutation_key(self) -> str:
        """
        Deterministic identity of the attempted mutation.

        Part 08 may use this identity for idempotency enforcement.
        This module does not store an idempotency registry.
        """
        return ":".join(
            (
                self.tenant_id,
                self.inventory_id,
                str(self.from_version),
                self.to_state.value,
                self.reservation_reference or "-",
                self.allocation_reference or "-",
            )
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "transition_id": self.transition_id,
            "tenant_id": self.tenant_id,
            "inventory_id": self.inventory_id,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "occurred_at": self.occurred_at.isoformat(),
            "reservation_reference": (
                self.reservation_reference
            ),
            "allocation_reference": (
                self.allocation_reference
            ),
        }

        return hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "tenant_id": self.tenant_id,
            "inventory_id": self.inventory_id,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "occurred_at": self.occurred_at.isoformat(),
            "reservation_reference": (
                self.reservation_reference
            ),
            "allocation_reference": (
                self.allocation_reference
            ),
            "mutation_key": self.mutation_key,
            "fingerprint": self.fingerprint,
        }


def allowed_availability_targets(
    state: AvailabilityState,
) -> frozenset[AvailabilityState]:
    try:
        state = AvailabilityState(state)
    except (TypeError, ValueError) as exc:
        raise InventoryAvailabilityError(
            "Invalid availability state."
        ) from exc

    return AVAILABILITY_TRANSITIONS[state]


def assert_availability_transition(
    current: AvailabilityState,
    target: AvailabilityState,
) -> None:
    try:
        current = AvailabilityState(current)
        target = AvailabilityState(target)
    except (TypeError, ValueError) as exc:
        raise InvalidAvailabilityTransition(
            "Availability state is invalid."
        ) from exc

    if current == target:
        raise InvalidAvailabilityTransition(
            f"Inventory is already {current.value}."
        )

    if target not in AVAILABILITY_TRANSITIONS[current]:
        raise InvalidAvailabilityTransition(
            "Invalid inventory availability transition: "
            f"{current.value} -> {target.value}"
        )


# ---------------------------------------------------------------------------
# Base state mutation
# ---------------------------------------------------------------------------


def transition_inventory_availability(
    inventory: Inventory,
    *,
    target: AvailabilityState,
    expected_version: int,
    transition_id: str,
    reservation_reference: str | None = None,
    allocation_reference: str | None = None,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Apply one availability mutation using optimistic version checking.

    No retry is performed.
    No conflict is repaired.
    No persistence is performed.
    """
    if not isinstance(
        inventory,
        Inventory,
    ):
        raise InventoryAvailabilityError(
            "inventory must be canonical Inventory."
        )

    if (
        isinstance(
            expected_version,
            bool,
        )
        or not isinstance(
            expected_version,
            int,
        )
        or expected_version < 1
    ):
        raise AvailabilityVersionConflict(
            "expected_version must be positive integer."
        )

    if inventory.version != expected_version:
        raise AvailabilityVersionConflict(
            "Stale inventory availability update: "
            f"expected={expected_version}, "
            f"actual={inventory.version}"
        )

    assert_availability_transition(
        inventory.availability,
        target,
    )

    timestamp = (
        _utc_now()
        if at is None
        else _aware_time(
            at,
            "at",
        )
    )

    updated = replace(
        inventory,
        availability=AvailabilityState(target),
        updated_at=timestamp,
        version=inventory.version + 1,
    )

    transition = AvailabilityTransition(
        transition_id=transition_id,
        tenant_id=inventory.tenant_id,
        inventory_id=inventory.inventory_id,
        from_state=inventory.availability,
        to_state=AvailabilityState(target),
        from_version=inventory.version,
        to_version=updated.version,
        occurred_at=timestamp,
        reservation_reference=reservation_reference,
        allocation_reference=allocation_reference,
    )

    return updated, transition


# ---------------------------------------------------------------------------
# Reservation boundary
# ---------------------------------------------------------------------------


def reserve_inventory(
    inventory: Inventory,
    *,
    reservation_reference: str,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Reserve only currently AVAILABLE inventory.

    Reservation requires an explicit external reference.
    The module does not store reservation records.
    """
    reservation_reference = _text(
        reservation_reference,
        "reservation_reference",
    )

    if inventory.availability is not (
        AvailabilityState.AVAILABLE
    ):
        raise ReservationBoundaryError(
            "Only AVAILABLE inventory can be reserved."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.RESERVED,
        expected_version=expected_version,
        transition_id=transition_id,
        reservation_reference=reservation_reference,
        at=at,
    )


def release_reservation(
    inventory: Inventory,
    *,
    reservation_reference: str,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Release a reservation back to AVAILABLE.

    The reference is mandatory so an unscoped release cannot be issued.
    """
    reservation_reference = _text(
        reservation_reference,
        "reservation_reference",
    )

    if inventory.availability is not (
        AvailabilityState.RESERVED
    ):
        raise ReservationBoundaryError(
            "Only RESERVED inventory can release "
            "through the reservation boundary."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.AVAILABLE,
        expected_version=expected_version,
        transition_id=transition_id,
        reservation_reference=reservation_reference,
        at=at,
    )


# ---------------------------------------------------------------------------
# Allocation boundary
# ---------------------------------------------------------------------------


def allocate_inventory(
    inventory: Inventory,
    *,
    allocation_reference: str,
    reservation_reference: str,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Allocate only RESERVED inventory.

    Allocation is deliberately downstream of reservation.
    """
    allocation_reference = _text(
        allocation_reference,
        "allocation_reference",
    )

    reservation_reference = _text(
        reservation_reference,
        "reservation_reference",
    )

    if inventory.availability is not (
        AvailabilityState.RESERVED
    ):
        raise AllocationBoundaryError(
            "Only RESERVED inventory can be allocated."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.ALLOCATED,
        expected_version=expected_version,
        transition_id=transition_id,
        reservation_reference=reservation_reference,
        allocation_reference=allocation_reference,
        at=at,
    )


def release_allocation(
    inventory: Inventory,
    *,
    allocation_reference: str,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Release an allocation back to RESERVED.

    The release remains within the allocation boundary.
    """
    allocation_reference = _text(
        allocation_reference,
        "allocation_reference",
    )

    if inventory.availability is not (
        AvailabilityState.ALLOCATED
    ):
        raise AllocationBoundaryError(
            "Only ALLOCATED inventory can release "
            "through the allocation boundary."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.RESERVED,
        expected_version=expected_version,
        transition_id=transition_id,
        allocation_reference=allocation_reference,
        at=at,
    )


def mark_inventory_sold(
    inventory: Inventory,
    *,
    allocation_reference: str,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Final availability transition from ALLOCATED to SOLD.
    """
    allocation_reference = _text(
        allocation_reference,
        "allocation_reference",
    )

    if inventory.availability is not (
        AvailabilityState.ALLOCATED
    ):
        raise AllocationBoundaryError(
            "Inventory can be sold only after allocation."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.SOLD,
        expected_version=expected_version,
        transition_id=transition_id,
        allocation_reference=allocation_reference,
        at=at,
    )


# ---------------------------------------------------------------------------
# Administrative availability boundaries
# ---------------------------------------------------------------------------


def block_inventory(
    inventory: Inventory,
    *,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Block AVAILABLE, RESERVED or ALLOCATED inventory.

    Caller-level authorization remains outside this layer.
    """
    if inventory.availability not in {
        AvailabilityState.AVAILABLE,
        AvailabilityState.RESERVED,
        AvailabilityState.ALLOCATED,
    }:
        raise InvalidAvailabilityTransition(
            "Current availability cannot be blocked."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.BLOCKED,
        expected_version=expected_version,
        transition_id=transition_id,
        at=at,
    )


def unblock_inventory(
    inventory: Inventory,
    *,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Return BLOCKED inventory to AVAILABLE.
    """
    if inventory.availability is not (
        AvailabilityState.BLOCKED
    ):
        raise InvalidAvailabilityTransition(
            "Only BLOCKED inventory can be unblocked."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.AVAILABLE,
        expected_version=expected_version,
        transition_id=transition_id,
        at=at,
    )


def make_inventory_unavailable(
    inventory: Inventory,
    *,
    expected_version: int,
    transition_id: str,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    AvailabilityTransition,
]:
    """
    Move current AVAILABLE/BLOCKED inventory to UNAVAILABLE.
    """
    if inventory.availability not in {
        AvailabilityState.AVAILABLE,
        AvailabilityState.BLOCKED,
    }:
        raise InvalidAvailabilityTransition(
            "Only AVAILABLE or BLOCKED inventory "
            "can become UNAVAILABLE."
        )

    return transition_inventory_availability(
        inventory,
        target=AvailabilityState.UNAVAILABLE,
        expected_version=expected_version,
        transition_id=transition_id,
        at=at,
    )


__all__ = [
    "AvailabilityTransition",
    "AVAILABILITY_TRANSITIONS",
    "AvailabilityVersionConflict",
    "AvailabilityTenantViolation",
    "AllocationBoundaryError",
    "InvalidAvailabilityTransition",
    "InventoryAvailabilityError",
    "ReservationBoundaryError",
    "allowed_availability_targets",
    "assert_availability_transition",
    "allocate_inventory",
    "block_inventory",
    "make_inventory_unavailable",
    "mark_inventory_sold",
    "release_allocation",
    "release_reservation",
    "reserve_inventory",
    "transition_inventory_availability",
    "unblock_inventory",
]
