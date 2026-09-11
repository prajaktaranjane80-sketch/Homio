import pytest

from .loop_budget import (
    consume_budget,
    has_budget,
    remaining_budget,
)


class Dummy:
    total_work_budget = 10
    total_token_budget = 100
    total_context_budget = 100

    work_consumed = 2
    token_consumed = 20
    context_consumed = 10


def test_remaining_budget():
    assert remaining_budget(
        Dummy()
    ) == (
        8,
        80,
        90,
    )


def test_budget_available():
    assert has_budget(
        Dummy(),
        work=5,
        tokens=50,
        context=50,
    )


def test_over_budget_rejected():
    with pytest.raises(ValueError):
        consume_budget(
            Dummy(),
            work=9,
            tokens=0,
            context=0,
        )
