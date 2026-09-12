from .dependency_graph import DependencyGraph
from .readiness_engine import (
    calculate_readiness,
)
from .scheduler_models import (
    WorkState,
    WorkUnit,
)


def make(
    work_id,
    dependencies=(),
    state=WorkState.DECLARED,
):
    return WorkUnit(
        work_id=work_id,
        version="1.0",
        description=work_id,
        dependencies=tuple(dependencies),
        priority=1,
        work_cost=1,
        token_cost=1,
        context_cost=1,
        state=state,
    )


def test_root_is_ready():
    graph = DependencyGraph(
        (make("A"),)
    )

    ready, waiting, blocked, completed, failed = (
        calculate_readiness(graph)
    )

    assert ready == ("A",)
    assert waiting == ()
    assert blocked == ()
    assert completed == ()
    assert failed == ()
