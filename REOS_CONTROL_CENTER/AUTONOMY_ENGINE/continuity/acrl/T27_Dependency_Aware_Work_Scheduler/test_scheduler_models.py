from .scheduler_models import (
    SchedulerPolicy,
    SchedulerRequest,
    WorkState,
    WorkUnit,
)


def test_work_unit_serialization():
    work = WorkUnit(
        work_id="A",
        version="1.0",
        description="work",
        dependencies=(),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )

    data = work.to_dict()

    assert data["work_id"] == "A"
    assert data["state"] == WorkState.DECLARED.value


def test_request_serialization():
    work = WorkUnit(
        work_id="A",
        version="1.0",
        description="work",
        dependencies=(),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )

    request = SchedulerRequest(
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

    assert request.to_dict()["scheduler_id"] == "s1"
