from __future__ import annotations

from .continuity_identity import fingerprint
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityResult,
)
from .continuity_policy import (
    ContinuityPolicy,
)
from .continuity_provenance import (
    ContinuityProvenance,
)
from .continuity_recovery import (
    evaluate_recovery,
)
from .continuity_snapshot import (
    build_snapshot,
)
from .continuity_validation import (
    validate_evidence,
    validate_request,
)
from .continuity_store import (
    ContinuityIdentityConflict,
    ContinuityReplayError,
    ContinuityStore,
)


def _make_result(
    *,
    request: ContinuityRequest,
    decision: ContinuityDecision,
    reason: str,
    selected: tuple[
        ContinuityEvidence, ...
    ] = (),
    missing: tuple[str, ...] = (),
    stale: tuple[str, ...] = (),
    conflicts: tuple[str, ...] = (),
    snapshot=None,
    explanation: str = "",
) -> ContinuityResult:
    request_fingerprint = fingerprint(
        request.to_dict()
    )

    payload = {
        "recovery_id": request.recovery_id,
        "project_id": request.project_id,
        "decision": decision.value,
        "reason": reason,
        "selected": [
            item.evidence_id
            for item in selected
        ],
        "missing": list(missing),
        "stale": list(stale),
        "conflicts": list(conflicts),
        "snapshot": (
            snapshot.to_dict()
            if snapshot is not None
            else None
        ),
    }

    return ContinuityResult(
        schema_version="1.0",
        decision=decision,
        reason=reason,
        recovery_id=request.recovery_id,
        project_id=request.project_id,
        snapshot=snapshot,
        selected_evidence=selected,
        missing_evidence_ids=missing,
        stale_evidence_ids=stale,
        conflicting_evidence_ids=conflicts,
        request_fingerprint=request_fingerprint,
        recovery_fingerprint=fingerprint(
            payload
        ),
        explanation=explanation,
    )


def recover_continuity(
    *,
    request: ContinuityRequest,
    evidence_items: tuple[
        ContinuityEvidence, ...
    ],
    store: ContinuityStore,
    policy: ContinuityPolicy | None = None,
    project_context: dict | None = None,
) -> ContinuityResult:
    policy = (
        policy
        or ContinuityPolicy()
    )

    ContinuityProvenance().validate()

    try:
        validate_request(
            request,
            policy,
        )

        for evidence in evidence_items:
            validate_evidence(
                evidence,
                policy,
            )

    except Exception as exc:
        return _make_result(
            request=request,
            decision=(
                ContinuityDecision.FAIL_CLOSED
            ),
            reason="INVALID_INPUT",
            explanation=str(exc),
        )

    decision, conflicts, missing, stale, explanation = (
        evaluate_recovery(
            request=request,
            evidence_items=evidence_items,
            policy=policy,
        )
    )

    if decision is not ContinuityDecision.RECOVERED:
        return _make_result(
            request=request,
            decision=decision,
            reason=decision.value,
            conflicts=conflicts,
            missing=missing,
            stale=stale,
            explanation=explanation,
        )

    selected = tuple(
        item
        for item in evidence_items
        if item.evidence_id
        in request.evidence_ids
    )

    context = (
        project_context
        or {}
    )

    project_fingerprint = context.get(
        "project_fingerprint",
        request.expected_project_fingerprint,
    )

    state_fingerprint = context.get(
        "state_fingerprint",
        request.expected_state_fingerprint,
    )

    branch = context.get(
        "branch",
        request.expected_branch,
    )

    commit_sha = context.get(
        "commit_sha",
        request.expected_commit_sha,
    )

    phase = context.get(
        "phase",
        "UNKNOWN",
    )

    gate_id = context.get(
        "gate_id",
        "UNKNOWN",
    )

    gate_status = context.get(
        "gate_status",
        "UNKNOWN",
    )

    current_task = context.get(
        "current_task",
        "UNKNOWN",
    )

    current_subtask = context.get(
        "current_subtask",
        "UNKNOWN",
    )

    current_subtask_status = context.get(
        "current_subtask_status",
        "UNKNOWN",
    )

    completed_subtasks = tuple(
        context.get(
            "completed_subtasks",
            (),
        )
    )

    pending_subtasks = tuple(
        context.get(
            "pending_subtasks",
            (),
        )
    )

    evidence_fingerprints = tuple(
        item.content_fingerprint
        for item in selected
    )

    if (
        project_fingerprint
        != request.expected_project_fingerprint
    ):
        return _make_result(
            request=request,
            decision=(
                ContinuityDecision.INTEGRITY_FAILURE
            ),
            reason="PROJECT_FINGERPRINT_MISMATCH",
            selected=selected,
            explanation=(
                "Project identity does not match expected identity."
            ),
        )

    if (
        state_fingerprint
        != request.expected_state_fingerprint
    ):
        return _make_result(
            request=request,
            decision=(
                ContinuityDecision.INTEGRITY_FAILURE
            ),
            reason="STATE_FINGERPRINT_MISMATCH",
            selected=selected,
            explanation=(
                "State identity does not match expected identity."
            ),
        )

    if (
        branch
        != request.expected_branch
    ):
        return _make_result(
            request=request,
            decision=(
                ContinuityDecision.INTEGRITY_FAILURE
            ),
            reason="BRANCH_MISMATCH",
            selected=selected,
            explanation=(
                "Continuity branch differs from expected branch."
            ),
        )

    if (
        commit_sha
        != request.expected_commit_sha
    ):
        return _make_result(
            request=request,
            decision=(
                ContinuityDecision.INTEGRITY_FAILURE
            ),
            reason="COMMIT_MISMATCH",
            selected=selected,
            explanation=(
                "Continuity commit differs from expected commit."
            ),
        )

    snapshot = build_snapshot(
        request=request,
        project_id=request.project_id,
        project_fingerprint=project_fingerprint,
        state_fingerprint=state_fingerprint,
        branch=branch,
        commit_sha=commit_sha,
        phase=phase,
        gate_id=gate_id,
        gate_status=gate_status,
        current_task=current_task,
        current_subtask=current_subtask,
        current_subtask_status=current_subtask_status,
        completed_subtasks=completed_subtasks,
        pending_subtasks=pending_subtasks,
        evidence_fingerprints=evidence_fingerprints,
        execution_checkpoint_id=(
            request.execution_checkpoint_id
        ),
        execution_checkpoint_fingerprint=(
            request.execution_checkpoint_fingerprint
        ),
    )

    result = _make_result(
        request=request,
        decision=ContinuityDecision.RECOVERED,
        reason="VALID",
        selected=selected,
        snapshot=snapshot,
        explanation=(
            "Authoritative cross-chat continuity recovered."
        ),
    )

    existing = store.get(
        request.recovery_id
    )

    if existing is not None:
        if (
            existing.recovery_fingerprint
            == result.recovery_fingerprint
        ):
            return ContinuityResult(
                schema_version=result.schema_version,
                decision=(
                    ContinuityDecision.READ_ONLY
                ),
                reason="EXISTING_IDENTICAL_RECOVERY",
                recovery_id=(
                    result.recovery_id
                ),
                project_id=result.project_id,
                snapshot=result.snapshot,
                selected_evidence=(
                    result.selected_evidence
                ),
                missing_evidence_ids=(
                    result.missing_evidence_ids
                ),
                stale_evidence_ids=(
                    result.stale_evidence_ids
                ),
                conflicting_evidence_ids=(
                    result.conflicting_evidence_ids
                ),
                request_fingerprint=(
                    result.request_fingerprint
                ),
                recovery_fingerprint=(
                    result.recovery_fingerprint
                ),
                explanation=(
                    "Identical continuity recovery "
                    "reused read-only."
                ),
            )

        return _make_result(
            request=request,
            decision=(
                ContinuityDecision.FAIL_CLOSED
            ),
            reason="RECOVERY_ID_COLLISION",
            selected=selected,
            snapshot=None,
            explanation=(
                "Recovery identity already exists with "
                "different authoritative content."
            ),
        )

    try:
        store.put(
            result
        )

    except ContinuityReplayError:
        return ContinuityResult(
            schema_version=result.schema_version,
            decision=(
                ContinuityDecision.READ_ONLY
            ),
            reason="REPLAY_REUSED",
            recovery_id=result.recovery_id,
            project_id=result.project_id,
            snapshot=result.snapshot,
            selected_evidence=(
                result.selected_evidence
            ),
            missing_evidence_ids=(
                result.missing_evidence_ids
            ),
            stale_evidence_ids=(
                result.stale_evidence_ids
            ),
            conflicting_evidence_ids=(
                result.conflicting_evidence_ids
            ),
            request_fingerprint=(
                result.request_fingerprint
            ),
            recovery_fingerprint=(
                result.recovery_fingerprint
            ),
            explanation=(
                "Identical continuity recovery "
                "already exists."
            ),
        )

    except ContinuityIdentityConflict:
        return _make_result(
            request=request,
            decision=(
                ContinuityDecision.FAIL_CLOSED
            ),
            reason="RECOVERY_ID_COLLISION",
            selected=selected,
            explanation=(
                "Recovery identity collision detected."
            ),
        )

    return result
