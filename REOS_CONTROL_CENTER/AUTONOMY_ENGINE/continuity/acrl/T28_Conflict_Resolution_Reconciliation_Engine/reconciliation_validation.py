from .reconciliation_models import ReconciliationRequest
from .reconciliation_policy import validate_policy


def validate_request(request: ReconciliationRequest) -> None:
    if not request.reconciliation_id.strip():
        raise ValueError("reconciliation_id required")

    if not request.scheduler_fingerprint.strip():
        raise ValueError("scheduler_fingerprint required")

    if not request.continuity_fingerprint.strip():
        raise ValueError("continuity_fingerprint required")

    if not request.evidence_fingerprint.strip():
        raise ValueError("evidence_fingerprint required")

    validate_policy(request.policy)

    ids = [c.conflict_id for c in request.conflicts]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate conflict_id")

    for conflict in request.conflicts:
        if not conflict.subject_id.strip():
            raise ValueError("subject_id required")
