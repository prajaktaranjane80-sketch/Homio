from .budget_models import (
    ContextWindow,
)


def test_context_window_usable_capacity():
    window = ContextWindow(
        declared_capacity=10000,
        safety_reserve=1000,
        minimum_operational_capacity=1000,
        compression_reserve=500,
    )

    assert (
        window.usable_capacity
        == 8500
    )


def test_reservation_remaining():
    from .budget_models import (
        BudgetReservation,
    )

    reservation = BudgetReservation(
        reservation_id="r",
        request_id="q",
        context_reserved=100,
        token_reserved=200,
        work_reserved=10,
        context_consumed=20,
        token_consumed=50,
        work_consumed=2,
    )

    assert (
        reservation.remaining()
        == (80, 150, 8)
    )
