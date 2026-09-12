from __future__ import annotations

from .dependency_graph import DependencyGraph
from .dependency_resolution import resolve_dependency
from .scheduler_models import (
    DependencyState,
    WorkState,
)


def calculate_readiness(
    graph: DependencyGraph,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    ready: list[str] = []
    waiting: list[str] = []
    blocked: list[str] = []
    completed: list[str] = []
    failed: list[str] = []

    for work_id in sorted(
        graph.work_units
    ):
        item = graph.work_units[work_id]

        if item.state == WorkState.COMPLETED:
            completed.append(work_id)
            continue

        if item.state == WorkState.FAILED:
            failed.append(work_id)
            continue

        if item.state == WorkState.BLOCKED:
            blocked.append(work_id)
            continue

        state = resolve_dependency(
            work_id,
            graph,
        )

        if state == DependencyState.SATISFIED:
            ready.append(work_id)

        elif state in {
            DependencyState.CONFLICT,
            DependencyState.INVALID,
            DependencyState.UNKNOWN,
        }:
            blocked.append(work_id)

        else:
            waiting.append(work_id)

    return (
        tuple(ready),
        tuple(waiting),
        tuple(blocked),
        tuple(completed),
        tuple(failed),
    )
