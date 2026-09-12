from .scheduler_controller import (
    build_schedule,
)
from .scheduler_models import (
    SchedulerDecision,
    SchedulerPolicy,
    SchedulerRequest,
    WorkState,
    WorkUnit,
)
from .scheduler_store import (
    SchedulerStore,
)


def test_blocked_dependency():
    dependency = WorkUnit(
        work_id="A",
        version="1.0",
        description="A",
        dependencies=(),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
        state=WorkState.BLOCKED,
    )

    child = WorkUnit(
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
        scheduler_id="blocked",
        loop_id="loop",
        loop_fingerprint="loop",
        continuity_fingerprint="continuity",
        evidence_fingerprint="evidence",
        work_budget=10,
        token_budget=10,
        context_budget=10,
        work_units=(dependency, child),
        policy=SchedulerPolicy(),
    )

    result = build_schedule(
        request=request,
        store=SchedulerStore(),
    )

    assert (
        result.decision
        is SchedulerDecision.BLOCKED
    )
