from __future__ import annotations

from .budget_models import (
    BudgetReservation,
)


def create_reservation(
    *,
    reservation_id: str,
    request_id: str,
    amounts: tuple[int, int, int],
) -> BudgetReservation:
    context, token, work = amounts

    return BudgetReservation(
        reservation_id=reservation_id,
        request_id=request_id,
        context_reserved=context,
        token_reserved=token,
        work_reserved=work,
    )


def consume(
    reservation: BudgetReservation,
    *,
    context: int = 0,
    token: int = 0,
    work: int = 0,
) -> BudgetReservation:
    if reservation.released:
        raise ValueError(
            "Cannot consume a released reservation."
        )

    if min(
        context,
        token,
        work,
    ) < 0:
        raise ValueError(
            "Consumption cannot be negative."
        )

    remaining = reservation.remaining()

    if context > remaining[0]:
        raise ValueError(
            "Context budget exhausted."
        )

    if token > remaining[1]:
        raise ValueError(
            "Token budget exhausted."
        )

    if work > remaining[2]:
        raise ValueError(
            "Work budget exhausted."
        )

    return BudgetReservation(
        reservation_id=(
            reservation.reservation_id
        ),
        request_id=(
            reservation.request_id
        ),
        context_reserved=(
            reservation.context_reserved
        ),
        token_reserved=(
            reservation.token_reserved
        ),
        work_reserved=(
            reservation.work_reserved
        ),
        context_consumed=(
            reservation.context_consumed
            + context
        ),
        token_consumed=(
            reservation.token_consumed
            + token
        ),
        work_consumed=(
            reservation.work_consumed
            + work
        ),
        released=False,
    )


def release(
    reservation: BudgetReservation,
) -> BudgetReservation:
    if reservation.released:
        return reservation

    return BudgetReservation(
        reservation_id=(
            reservation.reservation_id
        ),
        request_id=(
            reservation.request_id
        ),
        context_reserved=0,
        token_reserved=0,
        work_reserved=0,
        context_consumed=(
            reservation.context_consumed
        ),
        token_consumed=(
            reservation.token_consumed
        ),
        work_consumed=(
            reservation.work_consumed
        ),
        released=True,
    )
