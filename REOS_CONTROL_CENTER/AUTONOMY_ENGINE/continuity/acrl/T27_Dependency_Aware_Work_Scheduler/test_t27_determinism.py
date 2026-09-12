from .scheduler_controller import (
    build_schedule,
)
from .scheduler_models import (
    SchedulerPolicy,
    SchedulerRequest,
    WorkUnit,
)
from .scheduler_store import (
    SchedulerStore,
)


def make_request(scheduler_id):
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
        scheduler_id=scheduler_id,
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


def test_same_input_same_schedule():
    first = build_schedule(
        request=make_request("s1"),
        store=SchedulerStore(),
    )

    second = build_schedule(
        request=make_request("s1"),
        store=SchedulerStore(),
    )

    assert (
        first.snapshot.schedule_fingerprint
        == second.snapshot.schedule_fingerprint
    )
