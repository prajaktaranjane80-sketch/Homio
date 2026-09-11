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


def test_budget_allocation():
    request = BudgetRequest(
        request_id="allocation-1",
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
        recovery_id="recovery",
        source_resolution_id="resolution",
    )

    result = allocate_work_budget(
        request=request,
        manager=BudgetManager(
            context_capacity=10000,
            token_capacity=10000,
            work_capacity=20,
        ),
        store=BudgetStore(),
    )

    assert (
        result.decision
        is BudgetDecision.ALLOCATED
    )

    assert (
        result.reservation
        is not None
    )
