from .concurrency_engine import (
    build_concurrency_groups,
)
from .dependency_graph import DependencyGraph
from .scheduler_models import WorkUnit


def make(work_id, priority):
    return WorkUnit(
        work_id=work_id,
        version="1.0",
        description=work_id,
        dependencies=(),
        priority=priority,
        work_cost=1,
        token_cost=1,
        context_cost=1,
    )


def test_serial_groups():
    graph = DependencyGraph(
        (
            make("A", 1),
            make("B", 2),
        )
    )

    groups = build_concurrency_groups(
        ("A", "B"),
        graph,
        max_parallel=2,
        allow_parallel=False,
    )

    assert groups == (
        ("B",),
        ("A",),
    )


def test_parallel_groups():
    graph = DependencyGraph(
        (
            make("A", 1),
            make("B", 2),
        )
    )

    groups = build_concurrency_groups(
        ("A", "B"),
        graph,
        max_parallel=2,
        allow_parallel=True,
    )

    assert groups == (
        ("B", "A"),
    )
