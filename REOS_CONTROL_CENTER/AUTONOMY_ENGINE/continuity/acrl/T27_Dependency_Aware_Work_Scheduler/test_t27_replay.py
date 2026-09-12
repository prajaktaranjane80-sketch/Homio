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
        scheduler_id="replay",
        loop_id="loop",
        loop_fingerprint="loop-fp",
        continuity_fingerprint="continuity-fp",
        evidence_fingerprint="evidence-fp",
        work_budget=10,
        token_budget=10,
        context_budget=10,
        work_units=(work,),
        policy=SchedulerPolicy(),
    )


def test_replay_detected():
    store = SchedulerStore()
    request = make_request()

    first = build_schedule(
        request=request,
        store=store,
    )

    second = build_schedule(
        request=request,
        store=store,
    )

    assert (
        first.decision
        is SchedulerDecision.SCHEDULED
    )

    assert (
        second.decision
        is SchedulerDecision.REPLAY_DETECTED
    )
