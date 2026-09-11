from .budget_manager import (
    BudgetManager,
)
from .budget_models import (
    BudgetReservation,
)


def test_reservation_reduces_remaining():
    manager = BudgetManager(
        context_capacity=1000,
        token_capacity=2000,
        work_capacity=10,
    )

    reservation = BudgetReservation(
        reservation_id="r",
        request_id="q",
        context_reserved=100,
        token_reserved=200,
        work_reserved=2,
    )

    manager.reserve(
        reservation
    )

    snapshot = manager.snapshot()

    assert (
        snapshot.context_remaining
        == 900
    )

    assert (
        snapshot.token_remaining
        == 1800
    )

    assert (
        snapshot.work_remaining
        == 8
    )


def test_snapshot_has_fingerprint():
    manager = BudgetManager(
        context_capacity=1000,
        token_capacity=2000,
        work_capacity=10,
    )

    snapshot = manager.snapshot()

    assert len(
        snapshot.snapshot_fingerprint
    ) == 64
