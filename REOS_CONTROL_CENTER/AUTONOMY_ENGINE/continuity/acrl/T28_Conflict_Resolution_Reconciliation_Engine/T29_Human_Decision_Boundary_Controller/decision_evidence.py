from .decision_models import HumanDecision


def evidence_is_sufficient(
    decision: HumanDecision,
    required_evidence_ids: tuple[str, ...],
) -> bool:
    if not required_evidence_ids:
        return True

    return set(required_evidence_ids).issubset(
        set(decision.evidence_ids)
    )
