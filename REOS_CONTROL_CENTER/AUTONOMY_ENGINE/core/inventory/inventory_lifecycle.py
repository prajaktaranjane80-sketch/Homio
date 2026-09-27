"""
CORE-004 T04 — Inventory Lifecycle

Owns:
- draft
- active
- reserved
- blocked
- sold
- unavailable
- archived
- lifecycle transition rules
- invalid transition rejection
- lifecycle history

Does NOT own:
- availability transitions
- reservation engine
- allocation engine
- provenance
- commercial attributes
- concurrency coordinator
- authorization policy
- event transport
- REOS Control Center state
- ACRL execution

Lifecycle transitions are immutable transformations of the canonical
Inventory object. No persistence is performed here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .inventory import (
    Inventory,
    LifecycleState,
)


class InventoryLifecycleError(ValueError):
    """Base lifecycle error."""


class InvalidLifecycleTransition(
    InventoryLifecycleError
):
    """Raised when a lifecycle transition is not allowed."""


class LifecycleTenantViolation(
    InventoryLifecycleError
):
    """Raised when tenant context does not match inventory."""


class LifecycleVersionConflict(
    InventoryLifecycleError
):
    """Raised when the supplied version is stale."""


class LifecycleHistoryError(
    InventoryLifecycleError
):
    """Raised when lifecycle history is invalid."""


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
        raise InventoryLifecycleError(
            f"{name} must be datetime."
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise InventoryLifecycleError(
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
        raise InventoryLifecycleError(
            f"{name} must be string."
        )

    value = value.strip()

    if not value:
        raise InventoryLifecycleError(
            f"{name} cannot be empty."
        )

    return value


def _canonical_json(
    payload: Mapping[str, Any],
) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Canonical transition graph
# ---------------------------------------------------------------------------


LIFECYCLE_TRANSITIONS: Mapping[
    LifecycleState,
    frozenset[LifecycleState],
] = {
    LifecycleState.DRAFT: frozenset(
        {
            LifecycleState.ACTIVE,
            LifecycleState.BLOCKED,
            LifecycleState.ARCHIVED,
        }
    ),
    LifecycleState.ACTIVE: frozenset(
        {
            LifecycleState.RESERVED,
            LifecycleState.BLOCKED,
            LifecycleState.SOLD,
            LifecycleState.UNAVAILABLE,
            LifecycleState.ARCHIVED,
        }
    ),
    LifecycleState.RESERVED: frozenset(
        {
            LifecycleState.ACTIVE,
            LifecycleState.BLOCKED,
            LifecycleState.SOLD,
            LifecycleState.UNAVAILABLE,
            LifecycleState.ARCHIVED,
        }
    ),
    LifecycleState.BLOCKED: frozenset(
        {
            LifecycleState.ACTIVE,
            LifecycleState.UNAVAILABLE,
            LifecycleState.ARCHIVED,
        }
    ),
    LifecycleState.SOLD: frozenset(
        {
            LifecycleState.ARCHIVED,
        }
    ),
    LifecycleState.UNAVAILABLE: frozenset(
        {
            LifecycleState.ACTIVE,
            LifecycleState.BLOCKED,
            LifecycleState.ARCHIVED,
        }
    ),
    LifecycleState.ARCHIVED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class InventoryLifecycleHistory:
    """
    Immutable lifecycle transition record.

    This is a domain record, not a history database.
    """

    transition_id: str
    tenant_id: str
    inventory_id: str
    from_state: LifecycleState
    to_state: LifecycleState
    from_version: int
    to_version: int
    occurred_at: datetime
    actor_reference: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.transition_id,
            str,
        ) or not self.transition_id.strip():
            raise LifecycleHistoryError(
                "transition_id is required."
            )

        if not isinstance(
            self.tenant_id,
            str,
        ) or not self.tenant_id.strip():
            raise LifecycleHistoryError(
                "tenant_id is required."
            )

        if not isinstance(
            self.inventory_id,
            str,
        ) or not self.inventory_id.strip():
            raise LifecycleHistoryError(
                "inventory_id is required."
            )

        try:
            from_state = LifecycleState(
                self.from_state
            )
            to_state = LifecycleState(
                self.to_state
            )
        except (TypeError, ValueError) as exc:
            raise LifecycleHistoryError(
                "Invalid lifecycle state."
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
            isinstance(
                self.from_version,
                bool,
            )
            or not isinstance(
                self.from_version,
                int,
            )
            or self.from_version < 1
        ):
            raise LifecycleHistoryError(
                "from_version must be >= 1."
            )

        if (
            isinstance(
                self.to_version,
                bool,
            )
            or not isinstance(
                self.to_version,
                int,
            )
            or self.to_version
            != self.from_version + 1
        ):
            raise LifecycleHistoryError(
                "Lifecycle transition must increment "
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
            "actor_reference",
            _text(
                self.actor_reference,
                "actor_reference",
            ),
        )

        object.__setattr__(
            self,
            "reason",
            _text(
                self.reason,
                "reason",
            ),
        )

    @property
    def history_key(self) -> tuple[str, str, int]:
        return (
            self.tenant_id,
            self.inventory_id,
            self.to_version,
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
            "actor_reference": self.actor_reference,
            "reason": self.reason,
        }

        return hashlib.sha256(
            _canonical_json(payload)
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
            "actor_reference": self.actor_reference,
            "reason": self.reason,
            "fingerprint": self.fingerprint,
        }


def allowed_lifecycle_targets(
    state: LifecycleState,
) -> frozenset[LifecycleState]:
    try:
        state = LifecycleState(state)
    except (TypeError, ValueError) as exc:
        raise InventoryLifecycleError(
            "Invalid lifecycle state."
        ) from exc

    return LIFECYCLE_TRANSITIONS[state]


def assert_lifecycle_transition(
    current: LifecycleState,
    target: LifecycleState,
) -> None:
    try:
        current = LifecycleState(current)
        target = LifecycleState(target)
    except (TypeError, ValueError) as exc:
        raise InvalidLifecycleTransition(
            "Lifecycle state is invalid."
        ) from exc

    if current == target:
        raise InvalidLifecycleTransition(
            f"Inventory is already in {current.value}."
        )

    if target not in (
        LIFECYCLE_TRANSITIONS[current]
    ):
        raise InvalidLifecycleTransition(
            "Invalid inventory lifecycle transition: "
            f"{current.value} -> {target.value}"
        )


def transition_inventory_lifecycle(
    inventory: Inventory,
    *,
    target: LifecycleState,
    expected_version: int,
    transition_id: str,
    actor_reference: str | None = None,
    reason: str | None = None,
    at: datetime | None = None,
) -> tuple[
    Inventory,
    InventoryLifecycleHistory,
]:
    """
    Apply one lifecycle transition.

    expected_version is mandatory to prevent a caller from mutating a stale
    Inventory snapshot.

    The operation changes lifecycle and aggregate version only.
    Availability coupling belongs to Part 05 / Part 08.
    """
    if not isinstance(
        inventory,
        Inventory,
    ):
        raise InventoryLifecycleError(
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
        raise LifecycleVersionConflict(
            "expected_version must be a positive integer."
        )

    if inventory.version != expected_version:
        raise LifecycleVersionConflict(
            "Stale inventory lifecycle update: "
            f"expected={expected_version}, "
            f"actual={inventory.version}"
        )

    assert_lifecycle_transition(
        inventory.lifecycle,
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

    new_version = inventory.version + 1

    updated = replace(
        inventory,
        lifecycle=LifecycleState(target),
        updated_at=timestamp,
        version=new_version,
    )

    history = InventoryLifecycleHistory(
        transition_id=transition_id,
        tenant_id=inventory.tenant_id,
        inventory_id=inventory.inventory_id,
        from_state=inventory.lifecycle,
        to_state=LifecycleState(target),
        from_version=inventory.version,
        to_version=new_version,
        occurred_at=timestamp,
        actor_reference=actor_reference,
        reason=reason,
    )

    return updated, history


def validate_lifecycle_history(
    history: tuple[
        InventoryLifecycleHistory, ...
    ],
) -> None:
    """
    Validate continuity of an already supplied lifecycle history.

    This does not persist history or search for missing records.
    """
    if not isinstance(
        history,
        tuple,
    ):
        raise LifecycleHistoryError(
            "history must be tuple."
        )

    previous_version: int | None = None
    previous_state: LifecycleState | None = None
    tenant_id: str | None = None
    inventory_id: str | None = None

    for entry in history:
        if not isinstance(
            entry,
            InventoryLifecycleHistory,
        ):
            raise LifecycleHistoryError(
                "Invalid lifecycle history entry."
            )

        if tenant_id is None:
            tenant_id = entry.tenant_id
        elif tenant_id != entry.tenant_id:
            raise LifecycleHistoryError(
                "Lifecycle history crosses tenants."
            )

        if inventory_id is None:
            inventory_id = entry.inventory_id
        elif inventory_id != entry.inventory_id:
            raise LifecycleHistoryError(
                "Lifecycle history crosses inventories."
            )

        if previous_version is not None:
            if entry.from_version != previous_version:
                raise LifecycleHistoryError(
                    "Lifecycle history version gap detected."
                )

            if entry.from_state != previous_state:
                raise LifecycleHistoryError(
                    "Lifecycle history state gap detected."
                )

        assert_lifecycle_transition(
            entry.from_state,
            entry.to_state,
        )

        previous_version = entry.to_version
        previous_state = entry.to_state


__all__ = [
    "InventoryLifecycleError",
    "InvalidLifecycleTransition",
    "LifecycleHistoryError",
    "LifecycleTenantViolation",
    "LifecycleVersionConflict",
    "InventoryLifecycleHistory",
    "LIFECYCLE_TRANSITIONS",
    "allowed_lifecycle_targets",
    "assert_lifecycle_transition",
    "transition_inventory_lifecycle",
    "validate_lifecycle_history",
]
