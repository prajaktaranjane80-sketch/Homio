def detect_residual_work(mission, proof, dependency_gaps: list[str]) -> tuple[str, ...]:
    residual = set(mission.unresolved_nodes)
    residual.update(mission.blocked_nodes)
    residual.update(dependency_gaps)
    residual.update(f"PROOF::{x}" for x in proof.failed)
    residual.update(f"MISSING_PROOF::{x}" for x in proof.missing)
    if mission.rejected_human_decision:
        residual.add("HUMAN_REJECTION")
    return tuple(sorted(residual))
