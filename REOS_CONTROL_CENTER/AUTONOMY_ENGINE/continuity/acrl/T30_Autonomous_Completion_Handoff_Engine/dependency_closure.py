def validate_dependency_closure(graph: dict, completed: set[str]) -> tuple[bool, list[str]]:
    gaps = []
    for node, deps in graph.items():
        if node in completed:
            gaps.extend(dep for dep in deps if dep not in completed)
    return (not gaps, sorted(set(gaps)))
