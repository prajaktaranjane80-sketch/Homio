import pytest

from .budget_reservation import (
    consume,
    create_reservation,
    release,
)


def test_consume_reservation():
    reservation = create_reservation(
        reservation_id="r",
        request_id="q",
        amounts=(100, 200, 10),
    )

    updated = consume(
        reservation,
        context=20,
        token=50,
        work=2,
    )

    assert (
        updated.remaining()
        == (80, 150, 8)
    )


def test_over_consumption_blocked():
    reservation = create_reservation(
        reservation_id="r",
        request_id="q",
        amounts=(100, 100, 10),
    )

    with pytest.raises(ValueError):
        consume(
            reservation,
            token=101,
        )


def test_release_is_terminal():
    reservation = create_reservation(
        reservation_id="r",
        request_id="q",
        amounts=(100, 100, 10),
    )

    released = release(
        reservation
    )

    assert released.released is True
    assert released.remaining() == (
        0,
        0,
        0,
    )
