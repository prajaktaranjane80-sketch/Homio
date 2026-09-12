from .dependency_graph import DependencyGraph
from .dependency_resolution import (
    resolve_dependency,
)
from .scheduler_models import (
    DependencyState,
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


def test_root_dependency_is_satisfied():
    graph = DependencyGraph(
        (make("A"),)
    )

    assert (
        resolve_dependency(
            "A",
            graph,
        )
        is DependencyState.SATISFIED
    )


def test_uncompleted_dependency_waits():
    graph = DependencyGraph(
        (
            make("A"),
            make("B", ("A",)),
        )
    )

    assert (
        resolve_dependency(
            "B",
            graph,
        )
        is DependencyState.UNSATISFIED
    )
