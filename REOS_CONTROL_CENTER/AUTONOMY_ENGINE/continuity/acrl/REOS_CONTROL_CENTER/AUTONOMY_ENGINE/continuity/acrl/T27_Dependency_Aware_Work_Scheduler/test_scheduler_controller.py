from .scheduler_controller import (
    build_schedule,
)
from .scheduler_models import (
    SchedulerPolicy,
    SchedulerRequest,
    SchedulerDecision,
    WorkUnit,
)
from .scheduler_store import (
    SchedulerStore,
)


def make_request():
    work = WorkUnit(
        work_id="A",
        version="1.0",
        description="A",
        dependencies=(),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )

    return SchedulerRequest(
        scheduler_id="s1",
        loop_id="l1",
        loop_fingerprint="loop",
        continuity_fingerprint="continuity",
        evidence_fingerprint="evidence",
        work_budget=10,
        token_budget=10,
        context_budget=10,
        work_units=(work,),
        policy=SchedulerPolicy(),
    )


def test_schedule_created():
    result = build_schedule(
        request=make_request(),
        store=SchedulerStore(),
    )

    assert result.decision is SchedulerDecision.SCHEDULED
    assert result.snapshot is not None
    assert result.snapshot.ready_work == ("A",)
