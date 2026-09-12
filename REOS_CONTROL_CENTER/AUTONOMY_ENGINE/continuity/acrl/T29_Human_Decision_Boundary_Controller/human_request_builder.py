from .decision_models import DecisionRequest


def build_human_request(request: DecisionRequest) -> dict:
    return {
        "decision_id": request.decision_id,
        "boundary_reason": request.boundary_reason,
        "reconciliation_fingerprint": request.reconciliation_fingerprint,
        "continuity_fingerprint": request.continuity_fingerprint,
        "evidence_fingerprint": request.evidence_fingerprint,
        "requested_decision_type": request.requested_decision_type.value,
        "policy_version": request.policy.policy_version,
        "status": "WAITING_FOR_HUMAN"
    }
