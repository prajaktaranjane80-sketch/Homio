from .decision_models import DecisionRequest, HumanDecision
from .decision_policy import validate_policy


def validate_request(request: DecisionRequest) -> None:
    if not request.decision_id.strip():
        raise ValueError("decision_id required")

    if not request.reconciliation_fingerprint.strip():
        raise ValueError("reconciliation_fingerprint required")

    if not request.continuity_fingerprint.strip():
        raise ValueError("continuity_fingerprint required")

    if not request.evidence_fingerprint.strip():
        raise ValueError("evidence_fingerprint required")

    if not request.boundary_reason.strip():
        raise ValueError("boundary_reason required")

    validate_policy(request.policy)


def validate_human_decision(decision: HumanDecision) -> None:
    if not decision.decision_id.strip():
        raise ValueError("decision_id required")

    if not decision.decided_by.strip():
        raise ValueError("decided_by required")

    if decision.decision_timestamp < 0:
        raise ValueError("decision_timestamp must be non-negative")

    if not decision.rationale.strip():
        raise ValueError("rationale required")

    if not decision.nonce.strip():
        raise ValueError("nonce required")
