from .dependency_graph import DependencyGraph
from .scheduler_models import WorkUnit


def work(
    work_id,
    dependencies=(),
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
    )


def test_valid_graph():
    graph = DependencyGraph(
        (
            work("A"),
            work("B", ("A",)),
        )
    )

    graph.validate_nodes()
    assert graph.detect_cycle() is False


def test_cycle_detected():
    graph = DependencyGraph(
        (
            work("A", ("B",)),
            work("B", ("A",)),
        )
    )

    assert graph.detect_cycle() is True
