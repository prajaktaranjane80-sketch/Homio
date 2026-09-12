from reconciliation_engine import reconcile_conflicts
from reconciliation_fingerprint import resolution_fingerprint
from reconciliation_guard import validate_authority
from reconciliation_identity import reconciliation_identity
from reconciliation_models import (
    ReconciliationDecision,
    ReconciliationResult,
    ReconciliationSnapshot,
    ReconciliationStatus,
)
from reconciliation_registry import validate_registry
from reconciliation_store import (
    ReconciliationIdentityCollision,
    ReconciliationReplayError,
    ReconciliationStore,
)
from reconciliation_validation import validate_request


_DEFAULT_STORE = ReconciliationStore()


def reconcile(request, *, store: ReconciliationStore | None = None) -> ReconciliationResult:
    validate_registry("1.0", "1.0")
    validate_request(request)

    validate_authority(
        continuity_fingerprint=request.continuity_fingerprint,
        evidence_fingerprint=request.evidence_fingerprint,
    )

    store = store or _DEFAULT_STORE

    identity = reconciliation_identity(
        reconciliation_id=request.reconciliation_id,
        scheduler_fingerprint=request.scheduler_fingerprint,
        continuity_fingerprint=request.continuity_fingerprint,
        evidence_fingerprint=request.evidence_fingerprint,
        policy_fingerprint=request.policy.policy_version,
    )

    try:
        decision, resolutions, unresolved = reconcile_conflicts(
            request.conflicts,
            policy=request.policy,
            evidence_ids=tuple(
                evidence_id
                for conflict in request.conflicts
                for evidence_id in conflict.evidence_ids
            ),
        )

        snapshot = ReconciliationSnapshot(
            reconciliation_id=request.reconciliation_id,
            status=(
                ReconciliationStatus.RECONCILED
                if decision == ReconciliationDecision.RECONCILED
                else ReconciliationStatus.BLOCKED
                if decision in {
                    ReconciliationDecision.NO_SAFE_RESOLUTION,
                    ReconciliationDecision.FAIL_CLOSED,
                }
                else ReconciliationStatus.WAITING
                if decision == ReconciliationDecision.HUMAN_DECISION_REQUIRED
                else ReconciliationStatus.ACTIVE
            ),
            decision=decision,
            resolutions=resolutions,
            unresolved_conflicts=unresolved,
            fingerprint=resolution_fingerprint(resolutions),
        )

        store.put(request.reconciliation_id, snapshot)

        return ReconciliationResult(
            snapshot=snapshot,
            audit={
                "identity": identity,
                "resolution_count": len(resolutions),
                "unresolved_count": len(unresolved),
            },
        )

    except ReconciliationReplayError:
        raise

    except ReconciliationIdentityCollision:
        raise
