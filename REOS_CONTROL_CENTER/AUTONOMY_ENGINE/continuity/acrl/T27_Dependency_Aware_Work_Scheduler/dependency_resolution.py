from __future__ import annotations

from .dependency_graph import DependencyGraph
from .scheduler_models import (
    DependencyState,
    WorkState,
)


def resolve_dependency(
    work_id: str,
    graph: DependencyGraph,
) -> DependencyState:
    item = graph.work_units[work_id]

    if not item.dependencies:
        return DependencyState.SATISFIED

    for dependency in item.dependencies:
        dependency_item = graph.work_units.get(
            dependency
        )

        if dependency_item is None:
            return DependencyState.INVALID

        if dependency_item.state in {
            WorkState.BLOCKED,
            WorkState.FAILED,
        }:
            return DependencyState.CONFLICT

        if dependency_item.state != WorkState.COMPLETED:
            return DependencyState.UNSATISFIED

    return DependencyState.SATISFIED
