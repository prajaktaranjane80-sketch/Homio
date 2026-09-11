from .budget_coordinator import (
    allocate_work_budget,
)
from .budget_manager import (
    BudgetManager,
)
from .budget_models import (
    BudgetRequest,
    ContextWindow,
)
from .budget_store import (
    BudgetStore,
)


def make_request():
    return BudgetRequest(
        request_id="deterministic",
        context_requested=1000,
        token_requested=2000,
        work_requested=5,
        context_window=ContextWindow(
            declared_capacity=10000,
            safety_reserve=1000,
            minimum_operational_capacity=1000,
        ),
        token_capacity=10000,
        work_capacity=20,
    )


def run():
    return allocate_work_budget(
        request=make_request(),
        manager=BudgetManager(
            context_capacity=10000,
            token_capacity=10000,
            work_capacity=20,
        ),
        store=BudgetStore(),
    )


def test_same_input_same_result():
    first = run()
    second = run()

    assert (
        first.result_fingerprint
        == second.result_fingerprint
    )
