def finality_allowed(state: str, proof_complete: bool, residual_work: tuple[str, ...], human_rejected: bool) -> bool:
    return state == "COMPLETED" and proof_complete and not residual_work and not human_rejected
