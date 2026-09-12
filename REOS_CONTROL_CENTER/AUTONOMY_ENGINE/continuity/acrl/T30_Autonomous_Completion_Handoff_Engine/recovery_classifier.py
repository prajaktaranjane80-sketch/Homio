def classify_recovery(*, checkpoint_valid: bool, execution_interrupted: bool, evidence_consistent: bool, human_rejected: bool) -> str:
    if human_rejected:
        return "HUMAN_REJECTION_STOP"
    if execution_interrupted and checkpoint_valid and evidence_consistent:
        return "RESUME"
    if execution_interrupted and not checkpoint_valid:
        return "RESTART_REQUIRED"
    if not evidence_consistent:
        return "RECONCILIATION_REQUIRED"
    return "NO_RECOVERY"
