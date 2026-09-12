def classify_blockers(mission, dependency_ok: bool, residual_work: tuple[str, ...]) -> str:
    if mission.rejected_human_decision:
        return "HUMAN_REJECTED"
    if not dependency_ok:
        return "DEPENDENCY_BLOCKED"
    if mission.blocked_nodes:
        return "NODE_BLOCKED"
    if residual_work:
        return "RESIDUAL_WORK"
    return "NONE"
