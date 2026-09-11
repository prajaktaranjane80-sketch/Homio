from .budget_models import (
    BudgetDecision,
    BudgetResult,
    BudgetSnapshot,
)
from .budget_store import (
    BudgetReplayError,
    BudgetStore,
)


def make_result():
    snapshot = BudgetSnapshot(
        schema_version="1.0",
        policy_version="1.0",
        context_capacity=1000,
        context_reserved=0,
        context_consumed=0,
        token_capacity=2000,
        token_reserved=0,
        token_consumed=0,
        work_capacity=10,
        work_reserved=0,
        work_consumed=0,
        context_remaining=1000,
        token_remaining=2000,
        work_remaining=10,
        exhausted=False,
        snapshot_fingerprint="a" * 64,
    )

    return BudgetResult(
        schema_version="1.0",
        decision=BudgetDecision.ALLOCATED,
        reason="VALID",
        request_id="q",
        snapshot=snapshot,
        reservation=None,
        request_fingerprint="b" * 64,
        result_fingerprint="c" * 64,
        handoff_required=False,
        explanation="ok",
    )


def test_replay_is_detected():
    store = BudgetStore()
    result = make_result()

    store.put(result)

    try:
        store.put(result)
        assert False
    except BudgetReplayError:
        assert True
