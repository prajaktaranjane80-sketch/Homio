import pytest

from .budget_manager import (
    BudgetManager,
    BudgetExhaustedError,
)
from .budget_models import (
    BudgetReservation,
)


def test_second_reservation_cannot_overrun_capacity():
    manager = BudgetManager(
        context_capacity=100,
        token_capacity=100,
        work_capacity=10,
    )

    first = BudgetReservation(
        reservation_id="first",
        request_id="q1",
        context_reserved=80,
        token_reserved=80,
        work_reserved=8,
    )

    manager.reserve(
        first
    )

    second = BudgetReservation(
        reservation_id="second",
        request_id="q2",
        context_reserved=30,
        token_reserved=30,
        work_reserved=3,
    )

    with pytest.raises(
        BudgetExhaustedError
    ):
        manager.reserve(
            second
        )
