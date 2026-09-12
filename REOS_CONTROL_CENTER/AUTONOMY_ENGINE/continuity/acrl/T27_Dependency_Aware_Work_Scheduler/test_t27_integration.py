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


def test_t26_to_t27_boundary():
    work_a = WorkUnit(
        work_id="A",
        version="1.0",
        description="first",
        dependencies=(),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )

    work_b = WorkUnit(
        work_id="B",
        version="1.0",
        description="second",
        dependencies=("A",),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )

    request = SchedulerRequest(
        scheduler_id="integration",
        loop_id="t26-loop",
        loop_fingerprint="t26-fp",
        continuity_fingerprint="t24-fp",
        evidence_fingerprint="t23-fp",
        work_budget=10,
        token_budget=10,
        context_budget=10,
        work_units=(work_a, work_b),
        policy=SchedulerPolicy(
            max_parallel=1,
            allow_parallel=False,
        ),
    )

    result = build_schedule(
        request=request,
        store=SchedulerStore(),
    )

    assert (
        result.decision
        is SchedulerDecision.SCHEDULED
    )

    assert (
        result.snapshot.ordered_work
        == ("A",)
    )
