from __future__ import annotations

from .dependency_graph import DependencyGraph


def build_concurrency_groups(
    ready_work: tuple[str, ...],
    graph: DependencyGraph,
    *,
    max_parallel: int,
    allow_parallel: bool,
) -> tuple[tuple[str, ...], ...]:
    if not ready_work:
        return ()

    ordered = tuple(
        sorted(
            ready_work,
            key=lambda item: (
                -graph.work_units[item].priority,
                item,
            ),
        )
    )

    if not allow_parallel:
        return tuple(
            (item,)
            for item in ordered
        )

    groups: list[tuple[str, ...]] = []

    for index in range(
        0,
        len(ordered),
        max_parallel,
    ):
        groups.append(
            ordered[
                index:index + max_parallel
            ]
        )

    return tuple(groups)
