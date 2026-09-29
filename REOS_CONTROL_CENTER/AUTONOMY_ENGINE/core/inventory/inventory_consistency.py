"""
CORE-004 T08 — Consistency & Concurrency

Owns:
- aggregate consistency
- optimistic versioning
- concurrent availability preconditions
- stale update rejection
- duplicate-command identity
- idempotency contract
- reservation race protection
- deterministic conflict detection

Does NOT own:
- persistence
- distributed locking infrastructure
- lifecycle transition rules
- availability state machine
- reservation storage
- authorization
- event transport
- REOS state
- ACRL execution

This module defines immutable preconditions and conflict rules. It does
not implement a second persistence/idempotency engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .inventory import (
    AvailabilityState,
    Inventory,
    LifecycleState,
)


class InventoryConsistencyError(
    ValueError
):
    """Base CORE-004 consistency error."""


class InventoryConcurrencyConflict(
    InventoryConsistencyError
):
    """Raised when a mutation is based on stale state."""


class DuplicateInventoryCommand(
    InventoryConsistencyError
):
    """Raised when one idempotency identity is reused incompatibly."""


class ReservationRaceConflict(
    InventoryConsistencyError
):
    """Raised when reservation preconditions are no longer true."""


class ConsistencyValidationError(
    InventoryConsistencyError
):
    """Raised when a consistency contract is malformed."""


def _text(
    value: str,
    name: str,
) -> str:
    if not isinstance(value, str):
        raise ConsistencyValidationError(
            f"{name} must be string."
        )

    value = value.strip()

    if not value:
        raise ConsistencyValidationError(
            f"{name} cannot be empty."
        )

    return value


@dataclass(frozen=True, slots=True)
class InventoryConsistencySnapshot:
    """
    Immutable snapshot of the state used as mutation precondition.
    """

    tenant_id: str
    inventory_id: str
    version: int
    lifecycle: LifecycleState
    availability: AvailabilityState
    identity_fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        if (
            not isinstance(
                self.version,
                int,
            )
            or self.version < 1
        ):
            raise ConsistencyValidationError(
                "version must be >= 1."
            )

        try:
            lifecycle = LifecycleState(
                self.lifecycle
            )
            availability = AvailabilityState(
                self.availability
            )
        except (TypeError, ValueError) as exc:
            raise ConsistencyValidationError(
                "Invalid inventory state in snapshot."
            ) from exc

        object.__setattr__(
            self,
            "lifecycle",
            lifecycle,
        )

        object.__setattr__(
            self,
            "availability",
            availability,
        )

        object.__setattr__(
            self,
            "identity_fingerprint",
            _text(
                self.identity_fingerprint,
                "identity_fingerprint",
            ),
        )

    @classmethod
    def capture(
        cls,
        inventory: Inventory,
    ) -> "InventoryConsistencySnapshot":
        if not isinstance(
            inventory,
            Inventory,
        ):
            raise ConsistencyValidationError(
                "inventory must be Inventory."
            )

        return cls(
            tenant_id=inventory.tenant_id,
            inventory_id=inventory.inventory_id,
            version=inventory.version,
            lifecycle=inventory.lifecycle,
            availability=inventory.availability,
            identity_fingerprint=(
                inventory.identity_fingerprint
            ),
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": self.tenant_id,
            "inventory_id": self.inventory_id,
            "version": self.version,
            "lifecycle": self.lifecycle.value,
            "availability": self.availability.value,
            "identity_fingerprint": (
                self.identity_fingerprint
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

    def assert_current(
        self,
        inventory: Inventory,
    ) -> None:
        current = type(self).capture(
            inventory
        )

        if current.tenant_id != self.tenant_id:
            raise InventoryConcurrencyConflict(
                "Inventory tenant changed."
            )

        if current.inventory_id != self.inventory_id:
            raise InventoryConcurrencyConflict(
                "Inventory identity changed."
            )

        if current.version != self.version:
            raise InventoryConcurrencyConflict(
                "Inventory version changed."
            )

        if (
            current.identity_fingerprint
            != self.identity_fingerprint
        ):
            raise InventoryConcurrencyConflict(
                "Inventory immutable identity changed."
            )

        if current.lifecycle != self.lifecycle:
            raise InventoryConcurrencyConflict(
                "Inventory lifecycle changed."
            )

        if (
            current.availability
            != self.availability
        ):
            raise InventoryConcurrencyConflict(
                "Inventory availability changed."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "inventory_id": self.inventory_id,
            "version": self.version,
            "lifecycle": self.lifecycle.value,
            "availability": self.availability.value,
            "identity_fingerprint": (
                self.identity_fingerprint
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class InventoryMutationPrecondition:
    """
    Immutable optimistic-concurrency precondition.

    A caller must state what version it believes it is mutating.
    """

    tenant_id: str
    inventory_id: str
    expected_version: int
    expected_availability: AvailabilityState | None
    idempotency_key: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        if (
            not isinstance(
                self.expected_version,
                int,
            )
            or self.expected_version < 1
        ):
            raise ConsistencyValidationError(
                "expected_version must be >= 1."
            )

        if self.expected_availability is not None:
            try:
                object.__setattr__(
                    self,
                    "expected_availability",
                    AvailabilityState(
                        self.expected_availability
                    ),
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ConsistencyValidationError(
                    "expected_availability is invalid."
                ) from exc

        object.__setattr__(
            self,
            "idempotency_key",
            _text(
                self.idempotency_key,
                "idempotency_key",
            ),
        )

    def validate_snapshot(
        self,
        snapshot: InventoryConsistencySnapshot,
    ) -> None:
        if snapshot.tenant_id != self.tenant_id:
            raise InventoryConcurrencyConflict(
                "Precondition tenant mismatch."
            )

        if (
            snapshot.inventory_id
            != self.inventory_id
        ):
            raise InventoryConcurrencyConflict(
                "Precondition inventory mismatch."
            )

        if (
            snapshot.version
            != self.expected_version
        ):
            raise InventoryConcurrencyConflict(
                "Inventory version no longer satisfies "
                "the mutation precondition."
            )

        if (
            self.expected_availability is not None
            and snapshot.availability
            != self.expected_availability
        ):
            raise InventoryConcurrencyConflict(
                "Expected availability no longer matches "
                "current state."
            )


@dataclass(frozen=True, slots=True)
class InventoryCommandIdentity:
    """
    Deterministic identity of one mutation command.

    This does not store commands. It gives Part 08 / an external command
    store a stable idempotency identity.
    """

    tenant_id: str
    inventory_id: str
    operation: str
    idempotency_key: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        object.__setattr__(
            self,
            "operation",
            _text(
                self.operation,
                "operation",
            ),
        )

        object.__setattr__(
            self,
            "idempotency_key",
            _text(
                self.idempotency_key,
                "idempotency_key",
            ),
        )

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (
            self.tenant_id,
            self.inventory_id,
            self.operation,
            self.idempotency_key,
        )


@dataclass(frozen=True, slots=True)
class ReservationRacePrecondition:
    """
    Strong reservation precondition.

    A reservation can only proceed when all captured state still matches:
    tenant, inventory, version and AVAILABLE state.
    """

    tenant_id: str
    inventory_id: str
    expected_version: int
    expected_state: AvailabilityState = (
        AvailabilityState.AVAILABLE
    )
    reservation_reference: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        if (
            not isinstance(
                self.expected_version,
                int,
            )
            or self.expected_version < 1
        ):
            raise ReservationRaceConflict(
                "expected_version must be >= 1."
            )

        try:
            state = AvailabilityState(
                self.expected_state
            )
        except (TypeError, ValueError) as exc:
            raise ReservationRaceConflict(
                "expected_state is invalid."
            ) from exc

        object.__setattr__(
            self,
            "expected_state",
            state,
        )

        if state is not AvailabilityState.AVAILABLE:
            raise ReservationRaceConflict(
                "Reservation precondition must require AVAILABLE."
            )

        object.__setattr__(
            self,
            "reservation_reference",
            _text(
                self.reservation_reference,
                "reservation_reference",
            ),
        )

    def validate(
        self,
        inventory: Inventory,
    ) -> None:
        if inventory.tenant_id != self.tenant_id:
            raise ReservationRaceConflict(
                "Reservation tenant mismatch."
            )

        if inventory.inventory_id != self.inventory_id:
            raise ReservationRaceConflict(
                "Reservation inventory mismatch."
            )

        if inventory.version != self.expected_version:
            raise ReservationRaceConflict(
                "Reservation lost the version race."
            )

        if (
            inventory.availability
            is not self.expected_state
        ):
            raise ReservationRaceConflict(
                "Inventory is no longer AVAILABLE."
            )


def compare_command_identity(
    left: InventoryCommandIdentity,
    right: InventoryCommandIdentity,
) -> None:
    """
    Determine whether two commands may legally share an idempotency identity.

    Same identity + different operation is a conflict.
    Same identity + same operation is a duplicate candidate.

    Storage/replay decisions remain outside this module.
    """
    if not isinstance(
        left,
        InventoryCommandIdentity,
    ) or not isinstance(
        right,
        InventoryCommandIdentity,
    ):
        raise ConsistencyValidationError(
            "Both values must be InventoryCommandIdentity."
        )

    if (
        left.tenant_id == right.tenant_id
        and left.inventory_id == right.inventory_id
        and left.idempotency_key
        == right.idempotency_key
        and left.operation != right.operation
    ):
        raise DuplicateInventoryCommand(
            "Same idempotency identity was reused for "
            "different operations."
        )


def assert_single_writer_version(
    before: InventoryConsistencySnapshot,
    after: InventoryConsistencySnapshot,
) -> None:
    """
    Require exactly one aggregate version advance.
    """
    if before.tenant_id != after.tenant_id:
        raise InventoryConcurrencyConflict(
            "Tenant changed between versions."
        )

    if before.inventory_id != after.inventory_id:
        raise InventoryConcurrencyConflict(
            "Inventory identity changed between versions."
        )

    if after.version != before.version + 1:
        raise InventoryConcurrencyConflict(
            "Inventory version must advance exactly once."
        )


__all__ = [
    "InventoryConsistencyError",
    "InventoryConcurrencyConflict",
    "DuplicateInventoryCommand",
    "ReservationRaceConflict",
    "ConsistencyValidationError",
    "InventoryConsistencySnapshot",
    "InventoryMutationPrecondition",
    "InventoryCommandIdentity",
    "ReservationRacePrecondition",
    "compare_command_identity",
    "assert_single_writer_version",
]
