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


def test_exhaustion_is_blocked():
    request = BudgetRequest(
        request_id="too-large",
        context_requested=900,
        token_requested=900,
        work_requested=9,
        context_window=ContextWindow(
            declared_capacity=1000,
            safety_reserve=100,
            minimum_operational_capacity=100,
        ),
        token_capacity=1000,
        work_capacity=10,
    )

    result = allocate_work_budget(
        request=request,
        manager=BudgetManager(
            context_capacity=1000,
            token_capacity=1000,
            work_capacity=10,
        ),
        store=BudgetStore(),
    )

    assert result.decision in {
        BudgetDecision.EXHAUSTED,
        BudgetDecision.BLOCKED,
    }

    assert result.handoff_required is True
