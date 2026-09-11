from __future__ import annotations

from dataclasses import replace

from .loop_budget import (
    consume_budget,
)
from .loop_checkpoint import (
    validate_checkpoint_binding,
)
from .loop_guard import (
    evaluate_loop_guard,
)
from .loop_identity import (
    fingerprint,
    iteration_fingerprint,
)
from .loop_models import (
    ExecutionLoop,
    LoopDecision,
    LoopIteration,
    LoopRequest,
    LoopResult,
    LoopStatus,
)
from .loop_policy import (
    LoopPolicy,
)
from .loop_provenance import (
    LoopProvenance,
)
from .loop_registry import (
    LoopRegistry,
)
from .loop_store import (
    LoopIdentityConflict,
    LoopReplayError,
    LoopStore,
)
from .loop_validation import (
    validate_request,
)


def _result(
    *,
    decision: LoopDecision,
    reason: str,
    loop: ExecutionLoop | None,
    request: LoopRequest,
    next_layer: str | None,
    explanation: str,
) -> LoopResult:
    payload = {
        "decision": decision.value,
        "reason": reason,
        "loop": (
            loop.to_dict()
            if loop
            else None
        ),
        "next_layer": next_layer,
        "explanation": explanation,
    }

    return LoopResult(
        schema_version="1.0",
        decision=decision,
        reason=reason,
        loop=loop,
        request_fingerprint=fingerprint(
            request.to_dict()
        ),
        result_fingerprint=fingerprint(
            payload
        ),
        next_layer=next_layer,
        explanation=explanation,
    )


def _build_initial_loop(
    request: LoopRequest,
) -> ExecutionLoop:
    payload = {
        "schema_version": "1.0",
        "loop_version": "1.0",
        "loop_id": request.loop_id,
        "execution_intent": request.execution_intent,
        "checkpoint_id": request.checkpoint_id,
        "checkpoint_fingerprint": (
            request.checkpoint_fingerprint
        ),
        "continuity_recovery_id": (
            request.continuity_recovery_id
        ),
        "continuity_fingerprint": (
            request.continuity_fingerprint
        ),
        "evidence_resolution_id": (
            request.evidence_resolution_id
        ),
        "evidence_fingerprint": (
            request.evidence_fingerprint
        ),
        "max_iterations": request.max_iterations,
        "max_retries_per_iteration": (
            request.max_retries_per_iteration
        ),
        "no_progress_limit": request.no_progress_limit,
        "total_work_budget": request.total_work_budget,
        "total_token_budget": request.total_token_budget,
        "total_context_budget": (
            request.total_context_budget
        ),
    }

    return ExecutionLoop(
        schema_version="1.0",
        loop_version="1.0",
        loop_id=request.loop_id,
        status=LoopStatus.CREATED,
        execution_intent=request.execution_intent,
        checkpoint_id=request.checkpoint_id,
        checkpoint_fingerprint=(
            request.checkpoint_fingerprint
        ),
        continuity_recovery_id=(
            request.continuity_recovery_id
        ),
        continuity_fingerprint=(
            request.continuity_fingerprint
        ),
        evidence_resolution_id=(
            request.evidence_resolution_id
        ),
        evidence_fingerprint=(
            request.evidence_fingerprint
        ),
        max_iterations=request.max_iterations,
        max_retries_per_iteration=(
            request.max_retries_per_iteration
        ),
        current_iteration=0,
        total_work_budget=request.total_work_budget,
        total_token_budget=request.total_token_budget,
        total_context_budget=(
            request.total_context_budget
        ),
        work_consumed=0,
        token_consumed=0,
        context_consumed=0,
        no_progress_limit=request.no_progress_limit,
        no_progress_count=0,
        iterations=(),
        terminal_reason=None,
        loop_fingerprint=fingerprint(
            payload
        ),
    )


def _with_fingerprint(
    loop: ExecutionLoop,
) -> ExecutionLoop:
    payload = loop.to_dict()
    payload.pop(
        "loop_fingerprint",
        None,
    )

    return replace(
        loop,
        loop_fingerprint=fingerprint(
            payload
        ),
    )


def start_execution_loop(
    *,
    request: LoopRequest,
    store: LoopStore,
    policy: LoopPolicy | None = None,
    checkpoint_result=None,
    continuity_result=None,
    evidence_result=None,
    budget_result=None,
) -> LoopResult:
    policy = (
        policy
        or LoopPolicy()
    )

    LoopRegistry().validate()
    LoopProvenance().validate()

    try:
        validate_request(
            request,
            policy,
        )
    except Exception as exc:
        return _result(
            decision=LoopDecision.FAIL_CLOSED,
            reason="INVALID_REQUEST",
            loop=None,
            request=request,
            next_layer=None,
            explanation=str(exc),
        )

    try:
        if policy.require_checkpoint:
            if checkpoint_result is None:
                raise ValueError(
                    "T22 checkpoint is required."
                )

        if policy.require_continuity:
            continuity_decision = getattr(
                getattr(
                    continuity_result,
                    "decision",
                    None,
                ),
                "value",
                None,
            )

            if continuity_decision not in {
                "RECOVERED",
                "READ_ONLY",
            }:
                raise ValueError(
                    "T24 continuity is not recovered."
                )

        if policy.require_evidence:
            evidence_decision = getattr(
                getattr(
                    evidence_result,
                    "decision",
                    None,
                ),
                "value",
                None,
            )

            if evidence_decision not in {
                "RESOLVED",
                "READ_ONLY",
            }:
                raise ValueError(
                    "T23 evidence resolution is invalid."
                )

        if policy.require_budget:
            budget_decision = getattr(
                getattr(
                    budget_result,
                    "decision",
                    None,
                ),
                "value",
                None,
            )

            if budget_decision not in {
                "ALLOCATED",
                "READ_ONLY",
            }:
                raise ValueError(
                    "T25 budget is not allocated."
                )

        if checkpoint_result is not None:
            loop_probe = _build_initial_loop(
                request
            )

            validate_checkpoint_binding(
                loop_probe,
                checkpoint_result,
            )

    except Exception as exc:
        return _result(
            decision=LoopDecision.BLOCKED,
            reason="UPSTREAM_BOUNDARY_FAILURE",
            loop=None,
            request=request,
            next_layer=None,
            explanation=str(exc),
        )

    loop = _build_initial_loop(
        request
    )

        existing = store.get(
        request.loop_id
    )

    if existing is not None:
        same_identity = (
            existing.execution_intent
            == request.execution_intent
            and existing.checkpoint_id
            == request.checkpoint_id
            and existing.checkpoint_fingerprint
            == request.checkpoint_fingerprint
            and existing.continuity_recovery_id
            == request.continuity_recovery_id
            and existing.continuity_fingerprint
            == request.continuity_fingerprint
            and existing.evidence_resolution_id
            == request.evidence_resolution_id
            and existing.evidence_fingerprint
            == request.evidence_fingerprint
            and existing.max_iterations
            == request.max_iterations
            and existing.max_retries_per_iteration
            == request.max_retries_per_iteration
            and existing.no_progress_limit
            == request.no_progress_limit
            and existing.total_work_budget
            == request.total_work_budget
            and existing.total_token_budget
            == request.total_token_budget
            and existing.total_context_budget
            == request.total_context_budget
        )

        if same_identity:
            return _result(
                decision=LoopDecision.REPLAY_DETECTED,
                reason="LOOP_ALREADY_EXISTS",
                loop=existing,
                request=request,
                next_layer=None,
                explanation=(
                    "Identical autonomous execution loop "
                    "already exists."
                ),
            )

        return _result(
            decision=LoopDecision.FAIL_CLOSED,
            reason="LOOP_ID_COLLISION",
            loop=None,
            request=request,
            next_layer=None,
            explanation=(
                "Loop identity already exists with "
                "different immutable execution inputs."
            ),
        )

    loop = replace(
        loop,
        status=LoopStatus.RUNNING,
    )

    loop = _with_fingerprint(
        loop
    )

    try:
        store.put(
            loop
        )
    except LoopReplayError:
        return _result(
            decision=LoopDecision.REPLAY_DETECTED,
            reason="LOOP_REPLAY",
            loop=loop,
            request=request,
            next_layer=None,
            explanation=(
                "Identical loop already exists."
            ),
        )
    except LoopIdentityConflict as exc:
        return _result(
            decision=LoopDecision.FAIL_CLOSED,
            reason="LOOP_ID_COLLISION",
            loop=None,
            request=request,
            next_layer=None,
            explanation=str(exc),
        )

    return _result(
        decision=LoopDecision.STARTED,
        reason="VALID",
        loop=loop,
        request=request,
        next_layer="T27_Dependency_Aware_Work_Scheduler",
        explanation=(
            "Autonomous execution loop started. "
            "No execution was performed."
        ),
    )


def advance_execution_loop(
    *,
    loop: ExecutionLoop,
    store: LoopStore,
    progress_fingerprint: str,
    work_consumed: int = 0,
    token_consumed: int = 0,
    context_consumed: int = 0,
    retry_count: int = 0,
    completed: bool = False,
    blocked: bool = False,
    explanation: str = "",
) -> LoopResult:
    if loop.status not in {
        LoopStatus.RUNNING,
        LoopStatus.PAUSED,
    }:
        dummy_request = LoopRequest(
            loop_id=loop.loop_id,
            execution_intent=loop.execution_intent,
            checkpoint_id=loop.checkpoint_id,
            checkpoint_fingerprint=(
                loop.checkpoint_fingerprint
            ),
            continuity_recovery_id=(
                loop.continuity_recovery_id
            ),
            continuity_fingerprint=(
                loop.continuity_fingerprint
            ),
            evidence_resolution_id=(
                loop.evidence_resolution_id
            ),
            evidence_fingerprint=(
                loop.evidence_fingerprint
            ),
            max_iterations=loop.max_iterations,
            max_retries_per_iteration=(
                loop.max_retries_per_iteration
            ),
            no_progress_limit=loop.no_progress_limit,
            total_work_budget=loop.total_work_budget,
            total_token_budget=loop.total_token_budget,
            total_context_budget=loop.total_context_budget,
        )

        return _result(
            decision=LoopDecision.STOPPED,
            reason="TERMINAL_LOOP",
            loop=loop,
            request=dummy_request,
            next_layer=None,
            explanation=(
                "Terminal loop cannot be advanced."
            ),
        )

    if retry_count > loop.max_retries_per_iteration:
        dummy_request = LoopRequest(
            loop_id=loop.loop_id,
            execution_intent=loop.execution_intent,
            checkpoint_id=loop.checkpoint_id,
            checkpoint_fingerprint=loop.checkpoint_fingerprint,
            continuity_recovery_id=(
                loop.continuity_recovery_id
            ),
            continuity_fingerprint=(
                loop.continuity_fingerprint
            ),
            evidence_resolution_id=(
                loop.evidence_resolution_id
            ),
            evidence_fingerprint=(
                loop.evidence_fingerprint
            ),
            max_iterations=loop.max_iterations,
            max_retries_per_iteration=(
                loop.max_retries_per_iteration
            ),
            no_progress_limit=loop.no_progress_limit,
            total_work_budget=loop.total_work_budget,
            total_token_budget=loop.total_token_budget,
            total_context_budget=loop.total_context_budget,
        )

        return _result(
            decision=LoopDecision.FAIL_CLOSED,
            reason="RETRY_LIMIT_EXCEEDED",
            loop=loop,
            request=dummy_request,
            next_layer=None,
            explanation=(
                "Retry limit exceeded."
            ),
        )

    try:
        (
            new_work,
            new_tokens,
            new_context,
        ) = consume_budget(
            loop,
            work=work_consumed,
            tokens=token_consumed,
            context=context_consumed,
        )
    except ValueError as exc:
        new_loop = replace(
            loop,
            status=LoopStatus.EXHAUSTED,
            terminal_reason="BUDGET_EXHAUSTED",
        )

        new_loop = _with_fingerprint(
            new_loop
        )

        store.update(
            new_loop
        )

        dummy_request = LoopRequest(
            loop_id=loop.loop_id,
            execution_intent=loop.execution_intent,
            checkpoint_id=loop.checkpoint_id,
            checkpoint_fingerprint=loop.checkpoint_fingerprint,
            continuity_recovery_id=(
                loop.continuity_recovery_id
            ),
            continuity_fingerprint=(
                loop.continuity_fingerprint
            ),
            evidence_resolution_id=(
                loop.evidence_resolution_id
            ),
            evidence_fingerprint=(
                loop.evidence_fingerprint
            ),
            max_iterations=loop.max_iterations,
            max_retries_per_iteration=(
                loop.max_retries_per_iteration
            ),
            no_progress_limit=loop.no_progress_limit,
            total_work_budget=loop.total_work_budget,
            total_token_budget=loop.total_token_budget,
            total_context_budget=loop.total_context_budget,
        )

        return _result(
            decision=LoopDecision.BUDGET_EXHAUSTED,
            reason="BUDGET_EXHAUSTED",
            loop=new_loop,
            request=dummy_request,
            next_layer=None,
            explanation=str(exc),
        )

    previous_progress = (
        loop.iterations[-1].progress_fingerprint
        if loop.iterations
        else None
    )

    is_no_progress = (
        previous_progress
        == progress_fingerprint
        if previous_progress is not None
        else False
    )

    no_progress_count = (
        loop.no_progress_count + 1
        if is_no_progress
        else 0
    )

    iteration_number = (
        loop.current_iteration + 1
    )

    iteration_id = iteration_fingerprint(
        loop.loop_id,
        iteration_number,
        loop.checkpoint_fingerprint,
        loop.continuity_fingerprint,
    )

    iteration = LoopIteration(
        iteration=iteration_number,
        iteration_fingerprint=iteration_id,
        progress_fingerprint=progress_fingerprint,
        checkpoint_fingerprint=(
            loop.checkpoint_fingerprint
        ),
        continuity_fingerprint=(
            loop.continuity_fingerprint
        ),
        work_consumed=work_consumed,
        token_consumed=token_consumed,
        context_consumed=context_consumed,
        retry_count=retry_count,
        completed=completed,
        blocked=blocked,
        explanation=explanation,
    )

    new_status = LoopStatus.RUNNING
    decision = LoopDecision.CONTINUE
    reason = "PROGRESS"
    next_layer = (
        "T27_Dependency_Aware_Work_Scheduler"
    )
    terminal_reason = None

    if blocked:
        new_status = LoopStatus.PAUSED
        decision = LoopDecision.PAUSED
        reason = "BLOCKED_WORK"
        next_layer = (
            "T28_Conflict_Resolution_Reconciliation_Engine"
        )

    elif completed:
        new_status = LoopStatus.COMPLETED
        decision = LoopDecision.STOPPED
        reason = "LOOP_COMPLETED"
        next_layer = (
            "T30_Autonomous_Completion_Handoff_Engine"
        )

    elif no_progress_count >= loop.no_progress_limit:
        new_status = LoopStatus.FAILED
        decision = LoopDecision.NO_PROGRESS
        reason = "NO_PROGRESS"
        next_layer = (
            "T28_Conflict_Resolution_Reconciliation_Engine"
        )
        terminal_reason = (
            "No-progress safety threshold reached."
        )

    elif iteration_number >= loop.max_iterations:
        new_status = LoopStatus.STOPPED
        decision = LoopDecision.STOPPED
        reason = "ITERATION_LIMIT"
        next_layer = (
            "T29_Human_Decision_Boundary_Controller"
        )
        terminal_reason = (
            "Maximum iteration limit reached."
        )

    new_loop = replace(
        loop,
        status=new_status,
        current_iteration=iteration_number,
        work_consumed=new_work,
        token_consumed=new_tokens,
        context_consumed=new_context,
        no_progress_count=no_progress_count,
        iterations=(
            *loop.iterations,
            iteration,
        ),
        terminal_reason=terminal_reason,
    )

    new_loop = _with_fingerprint(
        new_loop
    )

    store.update(
        new_loop
    )

    dummy_request = LoopRequest(
        loop_id=loop.loop_id,
        execution_intent=loop.execution_intent,
        checkpoint_id=loop.checkpoint_id,
        checkpoint_fingerprint=loop.checkpoint_fingerprint,
        continuity_recovery_id=loop.continuity_recovery_id,
        continuity_fingerprint=loop.continuity_fingerprint,
        evidence_resolution_id=loop.evidence_resolution_id,
        evidence_fingerprint=loop.evidence_fingerprint,
        max_iterations=loop.max_iterations,
        max_retries_per_iteration=(
            loop.max_retries_per_iteration
        ),
        no_progress_limit=loop.no_progress_limit,
        total_work_budget=loop.total_work_budget,
        total_token_budget=loop.total_token_budget,
        total_context_budget=loop.total_context_budget,
    )

    return _result(
        decision=decision,
        reason=reason,
        loop=new_loop,
        request=dummy_request,
        next_layer=next_layer,
        explanation=explanation
        or "Loop iteration advanced without execution.",
    )
