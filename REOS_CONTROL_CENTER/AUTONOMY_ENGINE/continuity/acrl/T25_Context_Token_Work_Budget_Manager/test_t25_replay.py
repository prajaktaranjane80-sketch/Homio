from .budget_coordinator import (
    allocate_work_budget,
)
from .budget_manager import (
    BudgetManager,
)
from .budget_models import (
    BudgetDecision,
    BudgetRequest,
    ContextWindow,
)
from .budget_store import (
    BudgetStore,
)


def make_request():
    return BudgetRequest(
        request_id="same-request",
        context_requested=1000,
        token_requested=1000,
        work_requested=2,
        context_window=ContextWindow(
            declared_capacity=10000,
            safety_reserve=1000,
            minimum_operational_capacity=1000,
        ),
        token_capacity=10000,
        work_capacity=20,
    )


def test_identical_request_is_read_only_replay():
    request = make_request()

    manager = BudgetManager(
        context_capacity=10000,
        token_capacity=10000,
        work_capacity=20,
    )

    store = BudgetStore()

    first = allocate_work_budget(
        request=request,
        manager=manager,
        store=store,
    )

    second = allocate_work_budget(
        request=request,
        manager=manager,
        store=store,
    )

    assert (
        first.decision
        is BudgetDecision.ALLOCATED
    )

    assert (
        second.decision
        is BudgetDecision.READ_ONLY
    )
