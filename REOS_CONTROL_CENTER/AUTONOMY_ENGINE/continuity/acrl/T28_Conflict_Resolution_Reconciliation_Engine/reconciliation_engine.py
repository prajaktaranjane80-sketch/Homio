from reconciliation_models import (
    ReconciliationDecision,
    ReconciliationPolicy,
    Resolution,
    ResolutionKind,
)
from resolution_engine import resolve_conflict


def reconcile_conflicts(
    conflicts,
    *,
    policy: ReconciliationPolicy,
    evidence_ids: tuple[str, ...],
) -> tuple[ReconciliationDecision, tuple[Resolution, ...], tuple[str, ...]]:
    resolutions = []
    unresolved = []

    for conflict in sorted(conflicts, key=lambda item: item.conflict_id):
        resolution = resolve_conflict(
            conflict,
            evidence_ids=evidence_ids,
            allow_precedence=policy.allow_precedence_resolution,
        )

        if resolution is None:
            unresolved.append(conflict.conflict_id)
            continue

        resolutions.append(resolution)

    if unresolved:
        if policy.allow_human_boundary:
            return (
                ReconciliationDecision.HUMAN_DECISION_REQUIRED,
                tuple(resolutions),
                tuple(unresolved),
            )

        return (
            ReconciliationDecision.NO_SAFE_RESOLUTION,
            tuple(resolutions),
            tuple(unresolved),
        )

    if any(r.kind == ResolutionKind.FAIL_CLOSED for r in resolutions):
        return (
            ReconciliationDecision.FAIL_CLOSED,
            tuple(resolutions),
            (),
        )

    return (
        ReconciliationDecision.RECONCILED,
        tuple(resolutions),
        (),
    )
