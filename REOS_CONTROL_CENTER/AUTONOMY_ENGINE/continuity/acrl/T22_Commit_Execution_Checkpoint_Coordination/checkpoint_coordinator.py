from __future__ import annotations

from .checkpoint_authorization import (
    validate_authorization,
)
from .checkpoint_builder import (
    build_checkpoint,
)
from .checkpoint_identity import fingerprint
from .checkpoint_models import (
    CheckpointDecision,
    CheckpointRequest,
    CheckpointResult,
)
from .checkpoint_policy import (
    CheckpointPolicy,
)
from .checkpoint_provenance import (
    CheckpointProvenance,
)
from .checkpoint_registry import (
    CheckpointRegistry,
)
from .checkpoint_store import (
    CheckpointReplayError,
    CheckpointStore,
    CheckpointConcurrencyError,
)
from .checkpoint_validation import (
    validate_request,
)


def _result(
    *,
    decision: CheckpointDecision,
    reason: str,
    request_fingerprint: str,
    checkpoint=None,
    replay: bool = False,
    explanation: str = "",
) -> CheckpointResult:
    checkpoint_fingerprint = (
        checkpoint.checkpoint_fingerprint
        if checkpoint is not None
        else ""
    )

    return CheckpointResult(
        schema_version="1.0",
        decision=decision,
        reason=reason,
        checkpoint=checkpoint,
        checkpoint_fingerprint=(
            checkpoint_fingerprint
        ),
        request_fingerprint=(
            request_fingerprint
        ),
        replay=replay,
        explanation=explanation,
    )


def create_execution_checkpoint(
    *,
    request: CheckpointRequest,
    authorization,
    git_result,
    repair_result,
    store: CheckpointStore,
    policy: CheckpointPolicy | None = None,
) -> CheckpointResult:
    policy = policy or CheckpointPolicy()

    CheckpointRegistry().validate()
    CheckpointProvenance().validate()

    request_fingerprint = fingerprint(
        request.to_dict()
    )

    try:
        validate_request(
            request,
            policy,
        )
    except Exception as exc:
        return _result(
            decision=CheckpointDecision.INVALID,
            reason="INVALID_REQUEST",
            request_fingerprint=request_fingerprint,
            explanation=str(exc),
        )

    if policy.require_authorization:
        try:
            validate_authorization(
                authorization,
                expected_fingerprint=(
                    request.authorization_fingerprint
                ),
                expected_nonce=(
                    request.authorization_nonce
                ),
            )
        except Exception as exc:
            return _result(
                decision=CheckpointDecision.BLOCKED,
                reason="AUTHORIZATION_INVALID",
                request_fingerprint=request_fingerprint,
                explanation=str(exc),
            )

    if git_result is None:
        return _result(
            decision=CheckpointDecision.BLOCKED,
            reason="GIT_RESULT_REQUIRED",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T21 Git transaction result is required."
            ),
        )

    git_decision = getattr(
        getattr(
            git_result,
            "decision",
            None,
        ),
        "value",
        None,
    )

    if git_decision not in {
        "COMMITTED",
        "PUSHED",
    }:
        return _result(
            decision=CheckpointDecision.BLOCKED,
            reason="GIT_COMMIT_NOT_VERIFIED",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T21 result must be COMMITTED or PUSHED."
            ),
        )

    actual_commit = getattr(
        git_result,
        "commit_sha",
        None,
    )

    if actual_commit != request.expected_commit_sha:
        return _result(
            decision=CheckpointDecision.FAIL_CLOSED,
            reason="COMMIT_MISMATCH",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T21 commit SHA does not match checkpoint request."
            ),
        )

    actual_branch = getattr(
        git_result,
        "branch_after",
        None,
    )

    if actual_branch != request.expected_branch:
        return _result(
            decision=CheckpointDecision.FAIL_CLOSED,
            reason="BRANCH_MISMATCH",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T21 branch does not match checkpoint request."
            ),
        )

    if repair_result is None:
        return _result(
            decision=CheckpointDecision.BLOCKED,
            reason="REPAIR_RESULT_REQUIRED",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T20 repair result is required."
            ),
        )

    repair_decision = getattr(
        getattr(
            repair_result,
            "decision",
            None,
        ),
        "value",
        None,
    )

    if repair_decision != "VERIFIED":
        return _result(
            decision=CheckpointDecision.BLOCKED,
            reason="REPAIR_NOT_VERIFIED",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T20 repair must be VERIFIED."
            ),
        )

    repair_fingerprint = getattr(
        repair_result,
        "patch_fingerprint",
        None,
    )

    if (
        repair_fingerprint
        != request.repair_fingerprint
    ):
        return _result(
            decision=CheckpointDecision.FAIL_CLOSED,
            reason="REPAIR_FINGERPRINT_MISMATCH",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T20 repair fingerprint mismatch."
            ),
        )

    transaction_fingerprint = getattr(
        git_result,
        "transaction_fingerprint",
        None,
    )

    if (
        transaction_fingerprint
        != request.transaction_fingerprint
    ):
        return _result(
            decision=CheckpointDecision.FAIL_CLOSED,
            reason="TRANSACTION_FINGERPRINT_MISMATCH",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T21 transaction fingerprint mismatch."
            ),
        )

    if (
        request.checkpoint_kind.value
        == "EXECUTION"
        and policy.allow_execution
    ):
        return _result(
            decision=CheckpointDecision.INVALID,
            reason="INVALID_POLICY",
            request_fingerprint=request_fingerprint,
            explanation=(
                "T22 cannot authorize execution."
            ),
        )

    existing = store.get(
        request.checkpoint_id
    )

    if existing is not None:
        return _result(
            decision=CheckpointDecision.REPLAY_DETECTED,
            reason="CHECKPOINT_ALREADY_EXISTS",
            request_fingerprint=request_fingerprint,
            checkpoint=existing,
            replay=True,
            explanation=(
                "Checkpoint identity already exists."
            ),
        )

    checkpoint = build_checkpoint(
        request
    )

    try:
        store.put(
            checkpoint
        )
    except CheckpointReplayError:
        return _result(
            decision=CheckpointDecision.REPLAY_DETECTED,
            reason="CHECKPOINT_REPLAY",
            request_fingerprint=request_fingerprint,
            checkpoint=checkpoint,
            replay=True,
            explanation=(
                "Identical checkpoint already exists."
            ),
        )
    except CheckpointConcurrencyError as exc:
        return _result(
            decision=CheckpointDecision.FAIL_CLOSED,
            reason="CHECKPOINT_ID_COLLISION",
            request_fingerprint=request_fingerprint,
            explanation=str(exc),
        )

    return _result(
        decision=CheckpointDecision.CHECKPOINT_CREATED,
        reason="VALID",
        request_fingerprint=request_fingerprint,
        checkpoint=checkpoint,
        explanation=(
            "Immutable execution checkpoint created. "
            "No execution was performed."
        ),
    )
