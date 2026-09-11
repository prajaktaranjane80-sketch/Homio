from __future__ import annotations

from .budget_calculator import (
    allocate_amounts,
    calculate_available,
)
from .budget_identity import (
    fingerprint,
)
from .budget_manager import (
    BudgetExhaustedError,
    BudgetManager,
)
from .budget_models import (
    BudgetDecision,
    BudgetRequest,
    BudgetReservation,
    BudgetResult,
)
from .budget_policy import (
    BudgetPolicy,
)
from .budget_provenance import (
    BudgetProvenance,
)
from .budget_registry import (
    BudgetRegistry,
)
from .budget_reservation import (
    create_reservation,
)
from .budget_store import (
    BudgetIdentityConflict,
    BudgetReplayError,
    BudgetStore,
)
from .budget_validation import (
    validate_request,
)


def _result(
    *,
    request: BudgetRequest,
    decision: BudgetDecision,
    reason: str,
    snapshot,
    reservation: BudgetReservation | None,
    handoff_required: bool,
    explanation: str,
) -> BudgetResult:
    request_fingerprint = fingerprint(
        request.to_dict()
    )

    payload = {
        "request_id": request.request_id,
        "decision": decision.value,
        "reason": reason,
        "snapshot": snapshot.to_dict(),
        "reservation": (
            reservation.to_dict()
            if reservation
            else None
        ),
        "handoff_required": (
            handoff_required
        ),
    }

    return BudgetResult(
        schema_version="1.0",
        decision=decision,
        reason=reason,
        request_id=request.request_id,
        snapshot=snapshot,
        reservation=reservation,
        request_fingerprint=(
            request_fingerprint
        ),
        result_fingerprint=fingerprint(
            payload
        ),
        handoff_required=(
            handoff_required
        ),
        explanation=explanation,
    )


def allocate_work_budget(
    *,
    request: BudgetRequest,
    manager: BudgetManager,
    store: BudgetStore,
    policy: BudgetPolicy | None = None,
    continuity_result=None,
) -> BudgetResult:
    policy = (
        policy
        or BudgetPolicy()
    )

    BudgetRegistry().validate()
    BudgetProvenance().validate()

    try:
        validate_request(
            request,
            policy,
        )
    except Exception as exc:
        snapshot = manager.snapshot()

        return _result(
            request=request,
            decision=BudgetDecision.INVALID,
            reason="INVALID_REQUEST",
            snapshot=snapshot,
            reservation=None,
            handoff_required=True,
            explanation=str(exc),
        )

    if continuity_result is not None:
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
            snapshot = manager.snapshot()

            return _result(
                request=request,
                decision=BudgetDecision.BLOCKED,
                reason="CONTINUITY_NOT_RECOVERED",
                snapshot=snapshot,
                reservation=None,
                handoff_required=True,
                explanation=(
                    "T24 continuity must be recovered "
                    "before budget allocation."
                ),
            )

    existing = store.get(
        request.request_id
    )

    if existing is not None:
        return BudgetResult(
            schema_version=existing.schema_version,
            decision=BudgetDecision.READ_ONLY,
            reason="REPLAY_REUSED",
            request_id=existing.request_id,
            snapshot=existing.snapshot,
            reservation=existing.reservation,
            request_fingerprint=(
                existing.request_fingerprint
            ),
            result_fingerprint=(
                existing.result_fingerprint
            ),
            handoff_required=(
                existing.handoff_required
            ),
            explanation=(
                "Identical budget allocation "
                "reused read-only."
            ),
        )

    available = calculate_available(
        request,
        policy,
    )

    try:
        amounts = allocate_amounts(
            request=request,
            available=available,
            policy=policy,
        )
    except Exception as exc:
        snapshot = manager.snapshot()

        decision = (
            BudgetDecision.EXHAUSTED
            if "exceeds" in str(exc).lower()
            else BudgetDecision.BLOCKED
        )

        return _result(
            request=request,
            decision=decision,
            reason="BUDGET_UNAVAILABLE",
            snapshot=snapshot,
            reservation=None,
            handoff_required=True,
            explanation=str(exc),
        )

    reservation = create_reservation(
        reservation_id=(
            f"{request.request_id}:reservation"
        ),
        request_id=request.request_id,
        amounts=amounts,
    )

    try:
        manager.reserve(
            reservation
        )
    except BudgetExhaustedError as exc:
        snapshot = manager.snapshot()

        return _result(
            request=request,
            decision=BudgetDecision.EXHAUSTED,
            reason="RESERVATION_EXHAUSTED",
            snapshot=snapshot,
            reservation=None,
            handoff_required=True,
            explanation=str(exc),
        )
    except Exception as exc:
        snapshot = manager.snapshot()

        return _result(
            request=request,
            decision=BudgetDecision.FAIL_CLOSED,
            reason="RESERVATION_FAILURE",
            snapshot=snapshot,
            reservation=None,
            handoff_required=True,
            explanation=str(exc),
        )

    snapshot = manager.snapshot()

    result = _result(
        request=request,
        decision=BudgetDecision.ALLOCATED,
        reason="VALID",
        snapshot=snapshot,
        reservation=reservation,
        handoff_required=False,
        explanation=(
            "Context, token and work budget allocated "
            "within declared safe limits."
        ),
    )

    try:
        store.put(
            result
        )
    except BudgetReplayError:
        return result
    except BudgetIdentityConflict:
        return _result(
            request=request,
            decision=BudgetDecision.FAIL_CLOSED,
            reason="REQUEST_ID_COLLISION",
            snapshot=manager.snapshot(),
            reservation=None,
            handoff_required=True,
            explanation=(
                "Budget request identity collision detected."
            ),
        )

    return result
