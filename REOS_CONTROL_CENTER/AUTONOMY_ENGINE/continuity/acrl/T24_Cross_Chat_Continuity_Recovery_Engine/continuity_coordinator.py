from __future__ import annotations

from ..T23_Reference_Evidence_Resolution_Engine.evidence_identity import (
    fingerprint as t23_fingerprint,
)
from ..T23_Reference_Evidence_Resolution_Engine.evidence_models import (
    EvidenceStatus as T23EvidenceStatus,
    ResolutionDecision as T23ResolutionDecision,
    ResolutionRequest as T23ResolutionRequest,
)
from ..T23_Reference_Evidence_Resolution_Engine.resolution_store import (
    ResolutionStore as T23ResolutionStore,
)
from .continuity_evidence import select_current_evidence
from .continuity_identity import fingerprint
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityResult,
)
from .continuity_policy import ContinuityPolicy
from .continuity_provenance import ContinuityProvenance
from .continuity_recovery import evaluate_recovery
from .continuity_snapshot import build_snapshot
from .continuity_validation import (
    validate_evidence,
    validate_request,
)
from .continuity_store import (
    ContinuityIdentityConflict,
    ContinuityReplayError,
    ContinuityStore,
)


_CONTEXT_VALUE_FIELDS = (
    "project_fingerprint",
    "state_fingerprint",
    "branch",
    "commit_sha",
)

_UNRESOLVED_VALUES = frozenset(
    {
        "",
        "UNKNOWN",
        "UNAVAILABLE",
        "UNVERIFIED",
        "N/A",
        "NONE",
        "NULL",
    }
)

_REQUIRED_PROVENANCE = {
    "authority": "REOS_CONTROL_CENTER",
    "state_path": "REOS_CONTROL_CENTER/data/state.json",
    "project_fingerprint_source_layer": "T03",
    "state_fingerprint_source_layer": "T09",
    "branch_source_layer": "T21",
    "commit_sha_source_layer": "T21",
}


def _make_result(
    *,
    request: ContinuityRequest,
    decision: ContinuityDecision,
    reason: str,
    selected: tuple[ContinuityEvidence, ...] = (),
    missing: tuple[str, ...] = (),
    stale: tuple[str, ...] = (),
    conflicts: tuple[str, ...] = (),
    snapshot=None,
    explanation: str = "",
) -> ContinuityResult:
    request_fingerprint = fingerprint(request.to_dict())

    payload = {
        "recovery_id": request.recovery_id,
        "project_id": request.project_id,
        "decision": decision.value,
        "reason": reason,
        "selected": [item.evidence_id for item in selected],
        "missing": list(missing),
        "stale": list(stale),
        "conflicts": list(conflicts),
        "snapshot": snapshot.to_dict() if snapshot is not None else None,
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
        recovery_fingerprint=fingerprint(payload),
        explanation=explanation,
    )


def _read_only_replay(
    result: ContinuityResult,
    *,
    reason: str,
    explanation: str,
) -> ContinuityResult:
    return ContinuityResult(
        schema_version=result.schema_version,
        decision=ContinuityDecision.READ_ONLY,
        reason=reason,
        recovery_id=result.recovery_id,
        project_id=result.project_id,
        snapshot=result.snapshot,
        selected_evidence=result.selected_evidence,
        missing_evidence_ids=result.missing_evidence_ids,
        stale_evidence_ids=result.stale_evidence_ids,
        conflicting_evidence_ids=result.conflicting_evidence_ids,
        request_fingerprint=result.request_fingerprint,
        recovery_fingerprint=result.recovery_fingerprint,
        explanation=explanation,
    )


def _unresolved_authoritative_context_fields(
    project_context: object,
    request: ContinuityRequest,
) -> tuple[str, ...]:
    """Validate context shape and the upstream provenance contract."""

    if not isinstance(project_context, dict):
        return (*_CONTEXT_VALUE_FIELDS, "provenance")

    unresolved: list[str] = []

    for field_name in _CONTEXT_VALUE_FIELDS:
        value = project_context.get(field_name)

        if not isinstance(value, str):
            unresolved.append(field_name)
            continue

        if value.strip().upper() in _UNRESOLVED_VALUES:
            unresolved.append(field_name)

    provenance = project_context.get("provenance")

    if not isinstance(provenance, dict):
        return tuple(
            dict.fromkeys((*unresolved, "provenance"))
        )

    for field_name, expected_value in _REQUIRED_PROVENANCE.items():
        if provenance.get(field_name) != expected_value:
            unresolved.append(f"provenance.{field_name}")

    if provenance.get("source_resolution_id") != request.source_resolution_id:
        unresolved.append("provenance.source_resolution_id")

    evidence_ids = provenance.get("evidence_ids")

    if not isinstance(evidence_ids, (tuple, list)):
        unresolved.append("provenance.evidence_ids")
    elif tuple(evidence_ids) != request.evidence_ids:
        unresolved.append("provenance.evidence_ids")

    return tuple(dict.fromkeys(unresolved))


def _t23_resolution_failure(
    *,
    request: ContinuityRequest,
    evidence_items: tuple[ContinuityEvidence, ...],
    source_resolution_store: T23ResolutionStore | None,
) -> tuple[str, str] | None:
    """Verify the stored T23 result and bind each T24 evidence item to it.

    Caller-supplied provenance text is not accepted as a substitute for a
    stored T23 resolution. T23 must resolve the continuity scope
    ``continuity:<project_id>`` using the exact requested evidence IDs.
    """

    if not isinstance(source_resolution_store, T23ResolutionStore):
        return (
            "T23_RESOLUTION_REQUIRED",
            (
                "A trusted T23 ResolutionStore is required. Caller-supplied "
                "provenance claims cannot independently authorize recovery."
            ),
        )

    try:
        source_result = source_resolution_store.get(
            request.source_resolution_id
        )
    except Exception:
        return (
            "T23_RESOLUTION_INTEGRITY_FAILURE",
            "The T23 resolution store could not be read safely.",
        )

    if source_result is None:
        return (
            "T23_RESOLUTION_REQUIRED",
            (
                "No stored T23 resolution exists for the requested source "
                "resolution ID."
            ),
        )

    expected_subject = f"continuity:{request.project_id}"

    if (
        source_result.resolution_id != request.source_resolution_id
        or source_result.subject != expected_subject
    ):
        return (
            "T23_RESOLUTION_INTEGRITY_FAILURE",
            (
                "The stored T23 resolution identity or project scope does "
                "not match this continuity request."
            ),
        )

    expected_t23_request = T23ResolutionRequest(
        resolution_id=request.source_resolution_id,
        subject=expected_subject,
        evidence_ids=request.evidence_ids,
        require_current=True,
        require_canonical_when_available=True,
    )

    try:
        expected_request_fingerprint = t23_fingerprint(
            expected_t23_request.to_dict()
        )

        result_payload = {
            "resolution_id": source_result.resolution_id,
            "subject": source_result.subject,
            "decision": source_result.decision.value,
            "selected": (
                source_result.selected_evidence.evidence_id
                if source_result.selected_evidence is not None
                else None
            ),
            "candidates": [
                item.evidence_id
                for item in source_result.candidates
            ],
            "rejected": [
                item.evidence_id
                for item in source_result.rejected_evidence
            ],
            "conflicting": [
                item.evidence_id
                for item in source_result.conflicting_evidence
            ],
            "stale": [
                item.evidence_id
                for item in source_result.stale_evidence
            ],
            "missing": list(source_result.missing_evidence_ids),
        }

        expected_resolution_fingerprint = t23_fingerprint(
            result_payload
        )
    except Exception:
        return (
            "T23_RESOLUTION_INTEGRITY_FAILURE",
            "The stored T23 resolution could not be validated.",
        )

    if (
        source_result.request_fingerprint
        != expected_request_fingerprint
        or source_result.resolution_fingerprint
        != expected_resolution_fingerprint
    ):
        return (
            "T23_RESOLUTION_INTEGRITY_FAILURE",
            (
                "The stored T23 request or resolution fingerprint does not "
                "match its canonical contents."
            ),
        )

    if source_result.decision is not T23ResolutionDecision.RESOLVED:
        return (
            "T23_RESOLUTION_NOT_RESOLVED",
            (
                "T23 did not produce a RESOLVED result for the required "
                "continuity evidence."
            ),
        )

    if (
        source_result.selected_evidence is None
        or source_result.missing_evidence_ids
        or source_result.conflicting_evidence
        or source_result.stale_evidence
    ):
        return (
            "T23_RESOLUTION_NOT_RESOLVED",
            (
                "The T23 result lacks a clean current resolution or contains "
                "missing, conflicting, or stale evidence."
            ),
        )

    candidate_ids = tuple(
        item.evidence_id
        for item in source_result.candidates
    )

    if len(set(candidate_ids)) != len(candidate_ids):
        return (
            "T23_RESOLUTION_INTEGRITY_FAILURE",
            "The stored T23 result contains duplicate candidate IDs.",
        )

    candidates_by_id = {
        item.evidence_id: item
        for item in source_result.candidates
    }

    selected_id = source_result.selected_evidence.evidence_id

    if (
        selected_id not in candidates_by_id
        or candidates_by_id[selected_id]
        != source_result.selected_evidence
    ):
        return (
            "T23_RESOLUTION_INTEGRITY_FAILURE",
            "The T23 selected evidence is not present in its candidate set.",
        )

    continuity_by_id = {
        item.evidence_id: item
        for item in evidence_items
        if item.evidence_id in set(request.evidence_ids)
    }

    for evidence_id in request.evidence_ids:
        source_evidence = candidates_by_id.get(evidence_id)
        continuity_evidence = continuity_by_id.get(evidence_id)

        if source_evidence is None or continuity_evidence is None:
            return (
                "T23_EVIDENCE_BINDING_MISMATCH",
                (
                    "Every requested T24 evidence ID must exist in the "
                    "current T23 resolution candidate set."
                ),
            )

        if (
            source_evidence.subject != expected_subject
            or source_evidence.status is not T23EvidenceStatus.CURRENT
            or source_evidence.content_fingerprint
            != continuity_evidence.content_fingerprint
            or source_evidence.source_layer
            != continuity_evidence.source_layer
            or source_evidence.source_name
            != continuity_evidence.source_name
            or source_evidence.sequence != continuity_evidence.sequence
            or source_evidence.immutable != continuity_evidence.immutable
            or source_evidence.canonical != continuity_evidence.canonical
            or continuity_evidence.status.value != "CURRENT"
        ):
            return (
                "T23_EVIDENCE_BINDING_MISMATCH",
                (
                    "T24 evidence does not match the stored T23 evidence "
                    "identity, freshness, source, sequence, or fingerprint."
                ),
            )

    return None


def recover_continuity(
    *,
    request: ContinuityRequest,
    evidence_items: tuple[ContinuityEvidence, ...],
    store: ContinuityStore,
    policy: ContinuityPolicy | None = None,
    project_context: dict | None = None,
    source_resolution_store: T23ResolutionStore | None = None,
) -> ContinuityResult:
    policy = policy or ContinuityPolicy()

    try:
        ContinuityProvenance().validate()
        validate_request(request, policy)

        for evidence in evidence_items:
            validate_evidence(evidence, policy)

    except Exception as exc:
        return _make_result(
            request=request,
            decision=ContinuityDecision.FAIL_CLOSED,
            reason="INVALID_INPUT",
            explanation=str(exc),
        )

    decision, conflicts, missing, stale, explanation = evaluate_recovery(
        request=request,
        evidence_items=evidence_items,
        policy=policy,
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

    unresolved_fields = _unresolved_authoritative_context_fields(
        project_context,
        request,
    )

    if unresolved_fields:
        return _make_result(
            request=request,
            decision=ContinuityDecision.BLOCKED,
            reason="AUTHORITATIVE_CONTEXT_REQUIRED",
            explanation=(
                "Recovery requires independently observed context and "
                "the matching upstream source-provenance contract. "
                "Missing, unresolved, or mismatched fields: "
                f"{', '.join(unresolved_fields)}."
            ),
        )

    # Expected values are comparison inputs, never context fallbacks.
    assert isinstance(project_context, dict)
    context = project_context

    selected, _, _ = select_current_evidence(
        evidence_items,
        request.evidence_ids,
    )

    project_fingerprint = context["project_fingerprint"].strip()
    state_fingerprint = context["state_fingerprint"].strip()
    branch = context["branch"].strip()
    commit_sha = context["commit_sha"].strip()

    if project_fingerprint != request.expected_project_fingerprint:
        return _make_result(
            request=request,
            decision=ContinuityDecision.INTEGRITY_FAILURE,
            reason="PROJECT_FINGERPRINT_MISMATCH",
            selected=selected,
            explanation=(
                "Observed project identity does not match expected identity."
            ),
        )

    if state_fingerprint != request.expected_state_fingerprint:
        return _make_result(
            request=request,
            decision=ContinuityDecision.INTEGRITY_FAILURE,
            reason="STATE_FINGERPRINT_MISMATCH",
            selected=selected,
            explanation=(
                "Observed state identity does not match expected identity."
            ),
        )

    if branch != request.expected_branch:
        return _make_result(
            request=request,
            decision=ContinuityDecision.INTEGRITY_FAILURE,
            reason="BRANCH_MISMATCH",
            selected=selected,
            explanation=(
                "Observed continuity branch differs from expected branch."
            ),
        )

    if commit_sha != request.expected_commit_sha:
        return _make_result(
            request=request,
            decision=ContinuityDecision.INTEGRITY_FAILURE,
            reason="COMMIT_MISMATCH",
            selected=selected,
            explanation=(
                "Observed continuity commit differs from expected commit."
            ),
        )

    t23_failure = _t23_resolution_failure(
        request=request,
        evidence_items=evidence_items,
        source_resolution_store=source_resolution_store,
    )

    if t23_failure is not None:
        reason, failure_explanation = t23_failure
        failure_decision = (
            ContinuityDecision.FAIL_CLOSED
            if reason == "T23_RESOLUTION_INTEGRITY_FAILURE"
            else ContinuityDecision.BLOCKED
        )

        return _make_result(
            request=request,
            decision=failure_decision,
            reason=reason,
            selected=selected,
            explanation=failure_explanation,
        )

    snapshot = build_snapshot(
        request=request,
        project_id=request.project_id,
        project_fingerprint=project_fingerprint,
        state_fingerprint=state_fingerprint,
        branch=branch,
        commit_sha=commit_sha,
        phase=context.get("phase", "UNKNOWN"),
        gate_id=context.get("gate_id", "UNKNOWN"),
        gate_status=context.get("gate_status", "UNKNOWN"),
        current_task=context.get("current_task", "UNKNOWN"),
        current_subtask=context.get("current_subtask", "UNKNOWN"),
        current_subtask_status=context.get(
            "current_subtask_status",
            "UNKNOWN",
        ),
        completed_subtasks=tuple(context.get("completed_subtasks", ())),
        pending_subtasks=tuple(context.get("pending_subtasks", ())),
        evidence_fingerprints=tuple(
            item.content_fingerprint for item in selected
        ),
        execution_checkpoint_id=request.execution_checkpoint_id,
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
            "Authoritative cross-chat continuity recovered from verified "
            "current T23 resolution evidence."
        ),
    )

    existing = store.get(request.recovery_id)

    if existing is not None:
        if existing.recovery_fingerprint == result.recovery_fingerprint:
            return _read_only_replay(
                result,
                reason="EXISTING_IDENTICAL_RECOVERY",
                explanation=(
                    "Identical continuity recovery reused read-only."
                ),
            )

        return _make_result(
            request=request,
            decision=ContinuityDecision.FAIL_CLOSED,
            reason="RECOVERY_ID_COLLISION",
            selected=selected,
            explanation=(
                "Recovery identity already exists with different "
                "authoritative content."
            ),
        )

    try:
        store.put(result)

    except ContinuityReplayError:
        return _read_only_replay(
            result,
            reason="REPLAY_REUSED",
            explanation="Identical continuity recovery already exists.",
        )

    except ContinuityIdentityConflict:
        return _make_result(
            request=request,
            decision=ContinuityDecision.FAIL_CLOSED,
            reason="RECOVERY_ID_COLLISION",
            selected=selected,
            explanation="Recovery identity collision detected.",
        )

    return result
