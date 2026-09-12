from .scheduler_controller import (
    build_schedule,
)
from .scheduler_models import (
    SchedulerDecision,
    SchedulerPolicy,
    SchedulerRequest,
    WorkUnit,
)
from .scheduler_store import (
    SchedulerStore,
)


def test_cycle_is_rejected():
    a = WorkUnit(
        work_id="A",
        version="1.0",
        description="A",
        dependencies=("B",),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )

    b = WorkUnit(
        work_id="B",
        version="1.0",
        description="B",
        dependencies=("A",),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )

    request = SchedulerRequest(
        scheduler_id="cycle",
        loop_id="loop",
        loop_fingerprint="loop",
        continuity_fingerprint="continuity",
        evidence_fingerprint="evidence",
        work_budget=10,
        token_budget=10,
        context_budget=10,
        work_units=(a, b),
        policy=SchedulerPolicy(),
    )

    result = build_schedule(
        request=request,
        store=SchedulerStore(),
    )

    assert (
        result.decision
        is SchedulerDecision.DEPENDENCY_CYCLE
    )
