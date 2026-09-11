from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .budget_models import (
    BudgetReservation,
    BudgetSnapshot,
)
from .budget_policy import (
    BudgetPolicy,
)
from .budget_identity import (
    fingerprint,
)


class BudgetExhaustedError(RuntimeError):
    pass


class BudgetReservationConflict(RuntimeError):
    pass


@dataclass
class BudgetManager:
    context_capacity: int
    token_capacity: int
    work_capacity: int
    policy: BudgetPolicy = field(
        default_factory=BudgetPolicy
    )

    _reservations: dict[
        str,
        BudgetReservation,
    ] = field(
        default_factory=dict,
    )

    _lock: Lock = field(
        default_factory=Lock
    )

    def _totals(self) -> tuple[int, int, int]:
        context = sum(
            item.context_reserved
            for item in self._reservations.values()
            if not item.released
        )

        token = sum(
            item.token_reserved
            for item in self._reservations.values()
            if not item.released
        )

        work = sum(
            item.work_reserved
            for item in self._reservations.values()
            if not item.released
        )

        return (
            context,
            token,
            work,
        )

    def snapshot(
        self,
    ) -> BudgetSnapshot:
        with self._lock:
            reserved_context, reserved_token, reserved_work = (
                self._totals()
            )

            context_consumed = sum(
                item.context_consumed
                for item in self._reservations.values()
                if not item.released
            )

            token_consumed = sum(
                item.token_consumed
                for item in self._reservations.values()
                if not item.released
            )

            work_consumed = sum(
                item.work_consumed
                for item in self._reservations.values()
                if not item.released
            )

            context_remaining = max(
                0,
                self.context_capacity
                - reserved_context,
            )

            token_remaining = max(
                0,
                self.token_capacity
                - reserved_token,
            )

            work_remaining = max(
                0,
                self.work_capacity
                - reserved_work,
            )

            exhausted = (
                context_remaining <= 0
                or token_remaining <= 0
                or work_remaining <= 0
            )

            payload = {
                "schema_version": "1.0",
                "policy_version": (
                    self.policy.policy_version
                ),
                "context_capacity": (
                    self.context_capacity
                ),
                "context_reserved": (
                    reserved_context
                ),
                "context_consumed": (
                    context_consumed
                ),
                "token_capacity": (
                    self.token_capacity
                ),
                "token_reserved": (
                    reserved_token
                ),
                "token_consumed": (
                    token_consumed
                ),
                "work_capacity": (
                    self.work_capacity
                ),
                "work_reserved": (
                    reserved_work
                ),
                "work_consumed": (
                    work_consumed
                ),
                "context_remaining": (
                    context_remaining
                ),
                "token_remaining": (
                    token_remaining
                ),
                "work_remaining": (
                    work_remaining
                ),
                "exhausted": exhausted,
            }

            return BudgetSnapshot(
                schema_version="1.0",
                policy_version=(
                    self.policy.policy_version
                ),
                context_capacity=(
                    self.context_capacity
                ),
                context_reserved=(
                    reserved_context
                ),
                context_consumed=(
                    context_consumed
                ),
                token_capacity=(
                    self.token_capacity
                ),
                token_reserved=(
                    reserved_token
                ),
                token_consumed=(
                    token_consumed
                ),
                work_capacity=(
                    self.work_capacity
                ),
                work_reserved=(
                    reserved_work
                ),
                work_consumed=(
                    work_consumed
                ),
                context_remaining=(
                    context_remaining
                ),
                token_remaining=(
                    token_remaining
                ),
                work_remaining=(
                    work_remaining
                ),
                exhausted=exhausted,
                snapshot_fingerprint=fingerprint(
                    payload
                ),
            )

    def reserve(
        self,
        reservation: BudgetReservation,
    ) -> None:
        with self._lock:
            existing = self._reservations.get(
                reservation.reservation_id
            )

            if existing is not None:
                if existing == reservation:
                    raise BudgetReservationConflict(
                        "Identical reservation already exists."
                    )

                raise BudgetReservationConflict(
                    "Reservation identity collision."
                )

            snapshot = self.snapshot()

            remaining = (
                snapshot.context_remaining,
                snapshot.token_remaining,
                snapshot.work_remaining,
            )

            requested = (
                reservation.context_reserved,
                reservation.token_reserved,
                reservation.work_reserved,
            )

            if any(
                want > capacity
                for want, capacity
                in zip(
                    requested,
                    remaining,
                )
            ):
                raise BudgetExhaustedError(
                    "Requested reservation exceeds remaining budget."
                )

            self._reservations[
                reservation.reservation_id
            ] = reservation

    def get(
        self,
        reservation_id: str,
    ) -> BudgetReservation | None:
        with self._lock:
            return self._reservations.get(
                reservation_id
            )

    def update(
        self,
        reservation: BudgetReservation,
    ) -> None:
        with self._lock:
            if (
                reservation.reservation_id
                not in self._reservations
            ):
                raise KeyError(
                    "Unknown reservation."
                )

            self._reservations[
                reservation.reservation_id
            ] = reservation

    def release(
        self,
        reservation_id: str,
    ) -> BudgetReservation:
        with self._lock:
            reservation = self._reservations.get(
                reservation_id
            )

            if reservation is None:
                raise KeyError(
                    "Unknown reservation."
                )

            from .budget_reservation import (
                release,
            )

            released = release(
                reservation
            )

            self._reservations[
                reservation_id
            ] = released

            return released
