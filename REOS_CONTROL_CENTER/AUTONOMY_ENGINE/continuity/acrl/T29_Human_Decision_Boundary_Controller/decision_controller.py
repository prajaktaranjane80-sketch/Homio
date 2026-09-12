from .boundary_classifier import classify_boundary
from .decision_evidence import evidence_is_sufficient
from .decision_fingerprint import decision_record_fingerprint
from .decision_gate import evaluate_human_decision
from .decision_guard import validate_authority
from .decision_identity import decision_identity
from .decision_models import (
    BoundaryDecision,
    DecisionRequest,
    DecisionResult,
    HumanDecision,
)
from .decision_record import build_record
from .decision_registry import validate_registry
from .decision_store import (
    DecisionIdentityCollision,
    DecisionReplayError,
    DecisionStore,
)
from .decision_validation import (
    validate_human_decision,
    validate_request,
)


_DEFAULT_STORE = DecisionStore()


def create_decision_boundary(
    request: DecisionRequest,
    *,
    store: DecisionStore | None = None,
) -> DecisionResult:
    validate_registry("1.0", "1.0")
    validate_request(request)

    validate_authority(
        continuity_fingerprint=request.continuity_fingerprint,
        evidence_fingerprint=request.evidence_fingerprint,
    )

    boundary = classify_boundary(
        reconciliation_decision=request.reconciliation_decision,
        boundary_reason=request.boundary_reason,
        policy=request.policy,
    )

    identity = decision_identity(
        decision_id=request.decision_id,
        reconciliation_fingerprint=request.reconciliation_fingerprint,
        continuity_fingerprint=request.continuity_fingerprint,
        evidence_fingerprint=request.evidence_fingerprint,
        policy_fingerprint=request.policy.policy_version,
    )

    if boundary == BoundaryDecision.AUTONOMY_ALLOWED:
        record = build_record(
            decision_id=request.decision_id,
            boundary=boundary,
            decision=None,
            rationale="Autonomy allowed by policy.",
            fingerprint_value=identity,
        )
    else:
        record = build_record(
            decision_id=request.decision_id,
            boundary=BoundaryDecision.WAITING_FOR_HUMAN,
            decision=None,
            rationale=request.boundary_reason,
            fingerprint_value=identity,
        )

    store = store or _DEFAULT_STORE

    try:
        store.put(request.decision_id, record)
    except DecisionReplayError:
        raise
    except DecisionIdentityCollision:
        raise

    return DecisionResult(
        record=record,
        audit={
            "identity": identity,
            "boundary": boundary.value,
            "human_required": boundary == BoundaryDecision.HUMAN_REQUIRED,
        },
    )


def resolve_decision(
    request: DecisionRequest,
    decision: HumanDecision,
    *,
    required_evidence_ids: tuple[str, ...] = (),
    store: DecisionStore | None = None,
) -> DecisionResult:
    validate_registry("1.0", "1.0")
    validate_request(request)
    validate_human_decision(decision)

    validate_authority(
        continuity_fingerprint=request.continuity_fingerprint,
        evidence_fingerprint=request.evidence_fingerprint,
    )

    if decision.decision_id != request.decision_id:
        raise ValueError("decision id mismatch")

    if not evidence_is_sufficient(
        decision,
        required_evidence_ids,
    ):
        raise PermissionError("insufficient decision evidence")

    boundary = classify_boundary(
        reconciliation_decision=request.reconciliation_decision,
        boundary_reason=request.boundary_reason,
        policy=request.policy,
    )

    final_boundary = evaluate_human_decision(
        boundary=boundary,
        decision=decision,
    )

    identity = decision_identity(
        decision_id=request.decision_id,
        reconciliation_fingerprint=request.reconciliation_fingerprint,
        continuity_fingerprint=request.continuity_fingerprint,
        evidence_fingerprint=request.evidence_fingerprint,
        policy_fingerprint=request.policy.policy_version,
    )

    record = build_record(
        decision_id=request.decision_id,
        boundary=final_boundary,
        decision=decision,
        rationale=decision.rationale,
        fingerprint_value=identity,
    )

    final_fingerprint = decision_record_fingerprint(record)

    record = build_record(
        decision_id=request.decision_id,
        boundary=final_boundary,
        decision=decision,
        rationale=decision.rationale,
        fingerprint_value=final_fingerprint,
    )

    store = store or _DEFAULT_STORE

    try:
        existing = store.get(request.decision_id)

        if existing is None:
            store.put(request.decision_id, record)
        else:
            if existing.status == record.status:
                raise DecisionReplayError(
                    "decision already processed"
                )

            store._items[request.decision_id] = record

    except DecisionIdentityCollision:
        raise

    return DecisionResult(
        record=record,
        audit={
            "identity": identity,
            "final_fingerprint": final_fingerprint,
            "decision": final_boundary.value,
        },
    )
