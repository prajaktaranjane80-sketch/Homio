def unresolved_dependencies(graph: dict, completed: set[str]) -> list[str]:
    unresolved = []
    for node, deps in graph.items():
        if node in completed:
            continue
        missing = [dep for dep in deps if dep not in completed]
        if missing:
            unresolved.append(node)
    return sorted(unresolved)
