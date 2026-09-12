from __future__ import annotations

from dataclasses import replace

from .concurrency_engine import (
    build_concurrency_groups,
)
from .dependency_graph import (
    DependencyGraph,
)
from .readiness_engine import (
    calculate_readiness,
)
from .scheduler_fingerprint import (
    policy_fingerprint,
    schedule_fingerprint,
)
from .scheduler_guard import (
    validate_authority_boundary,
)
from .scheduler_identity import (
    fingerprint,
)
from .scheduler_models import (
    ScheduleSnapshot,
    SchedulerDecision,
    SchedulerRequest,
    SchedulerResult,
    SchedulerStatus,
    WorkState,
)
from .scheduler_policy import (
    validate_policy,
)
from .scheduler_registry import (
    SchedulerRegistry,
)
from .scheduler_store import (
    SchedulerIdentityConflict,
    SchedulerReplayError,
    SchedulerStore,
)
from .scheduler_validation import (
    validate_request,
)


def _result(
    *,
    decision: SchedulerDecision,
    snapshot: ScheduleSnapshot | None,
    request: SchedulerRequest,
    next_layer: str | None,
    explanation: str,
) -> SchedulerResult:
    payload = {
        "decision": decision.value,
        "snapshot": (
            snapshot.to_dict()
            if snapshot
            else None
        ),
        "next_layer": next_layer,
        "explanation": explanation,
    }

    return SchedulerResult(
        schema_version="1.0",
        decision=decision,
        snapshot=snapshot,
        request_fingerprint=fingerprint(
            request.to_dict()
        ),
        result_fingerprint=fingerprint(
            payload
        ),
        next_layer=next_layer,
        explanation=explanation,
    )


def register_work(
    *,
    work_units,
) -> tuple:
    return tuple(work_units)


def build_schedule(
    *,
    request: SchedulerRequest,
    store: SchedulerStore,
) -> SchedulerResult:
    registry = SchedulerRegistry()
    registry.validate()

    try:
        validate_policy(
            request.policy
        )
        validate_request(
            request
        )
        validate_authority_boundary(
            request
        )
    except Exception as exc:
        return _result(
            decision=SchedulerDecision.FAIL_CLOSED,
            snapshot=None,
            request=request,
            next_layer=None,
            explanation=str(exc),
        )

    graph = DependencyGraph(
        request.work_units
    )

    try:
        graph.validate_nodes()
    except Exception as exc:
        return _result(
            decision=SchedulerDecision.FAIL_CLOSED,
            snapshot=None,
            request=request,
            next_layer=None,
            explanation=str(exc),
        )

    if graph.detect_cycle():
        return _result(
            decision=SchedulerDecision.DEPENDENCY_CYCLE,
            snapshot=None,
            request=request,
            next_layer="T28_Conflict_Resolution_Reconciliation_Engine",
            explanation=(
                "Dependency cycle detected."
            ),
        )

    (
        ready,
        waiting,
        blocked,
        completed,
        failed,
    ) = calculate_readiness(
        graph
    )

    if blocked:
        status = SchedulerStatus.FAILED
        decision = SchedulerDecision.BLOCKED
        reason = "DEPENDENCY_BLOCKED"
        next_layer = (
            "T28_Conflict_Resolution_Reconciliation_Engine"
        )

    elif not ready:
        if waiting:
            status = SchedulerStatus.PAUSED
            decision = SchedulerDecision.WAITING
            reason = "WAITING_FOR_DEPENDENCIES"
            next_layer = (
                "T27_Dependency_Aware_Work_Scheduler"
            )
        else:
            status = SchedulerStatus.STOPPED
            decision = SchedulerDecision.STOPPED
            reason = "NO_REMAINING_WORK"
            next_layer = (
                "T30_Autonomous_Completion_Handoff_Engine"
            )

    else:
        estimated_work = sum(
            graph.work_units[item].work_cost
            for item in ready
        )

        estimated_tokens = sum(
            graph.work_units[item].token_cost
            for item in ready
        )

        estimated_context = sum(
            graph.work_units[item].context_cost
            for item in ready
        )

        if request.policy.require_budget and (
            estimated_work > request.work_budget
            or estimated_tokens
            > request.token_budget
            or estimated_context
            > request.context_budget
        ):
            status = SchedulerStatus.PAUSED
            decision = SchedulerDecision.RESOURCE_BLOCKED
            reason = "BUDGET_INSUFFICIENT"
            next_layer = (
                "T29_Human_Decision_Boundary_Controller"
            )
        else:
            status = SchedulerStatus.ACTIVE
            decision = SchedulerDecision.SCHEDULED
            reason = "READY"
            next_layer = (
                "T27_Dependency_Aware_Work_Scheduler"
            )

    groups = build_concurrency_groups(
        ready,
        graph,
        max_parallel=request.policy.max_parallel,
        allow_parallel=request.policy.allow_parallel,
    )

    ordered = tuple(
        item
        for group in groups
        for item in group
    )

    policy_fp = policy_fingerprint(
        request.policy
    )

    payload = {
        "scheduler_id": request.scheduler_id,
        "loop_id": request.loop_id,
        "status": status.value,
        "ready_work": list(ready),
        "waiting_work": list(waiting),
        "blocked_work": list(blocked),
        "completed_work": list(completed),
        "failed_work": list(failed),
        "ordered_work": list(ordered),
        "concurrency_groups": [
            list(group)
            for group in groups
        ],
        "graph_fingerprint": (
            graph.fingerprint()
        ),
        "policy_fingerprint": policy_fp,
        "reason": reason,
    }

    schedule_fp = schedule_fingerprint(
        payload
    )

    snapshot = ScheduleSnapshot(
        scheduler_id=request.scheduler_id,
        loop_id=request.loop_id,
        status=status,
        ready_work=ready,
        waiting_work=waiting,
        blocked_work=blocked,
        completed_work=completed,
        failed_work=failed,
        ordered_work=ordered,
        concurrency_groups=groups,
        graph_fingerprint=(
            graph.fingerprint()
        ),
        policy_fingerprint=policy_fp,
        schedule_fingerprint=schedule_fp,
        reason=reason,
    )

    existing = store.get(
        request.scheduler_id
    )

    if existing is not None:
        if (
            existing.schedule_fingerprint
            == snapshot.schedule_fingerprint
        ):
            return _result(
                decision=SchedulerDecision.REPLAY_DETECTED,
                snapshot=existing,
                request=request,
                next_layer=None,
                explanation=(
                    "Identical schedule already exists."
                ),
            )

        return _result(
            decision=SchedulerDecision.FAIL_CLOSED,
            snapshot=None,
            request=request,
            next_layer=None,
            explanation=(
                "Scheduler identity collision."
            ),
        )

    try:
        store.put(
            snapshot
        )
    except SchedulerReplayError:
        return _result(
            decision=SchedulerDecision.REPLAY_DETECTED,
            snapshot=snapshot,
            request=request,
            next_layer=None,
            explanation=(
                "Identical schedule already exists."
            ),
        )
    except SchedulerIdentityConflict as exc:
        return _result(
            decision=SchedulerDecision.FAIL_CLOSED,
            snapshot=None,
            request=request,
            next_layer=None,
            explanation=str(exc),
        )

    return _result(
        decision=decision,
        snapshot=snapshot,
        request=request,
        next_layer=next_layer,
        explanation=(
            f"Dependency-aware schedule created: {reason}."
        ),
    )
