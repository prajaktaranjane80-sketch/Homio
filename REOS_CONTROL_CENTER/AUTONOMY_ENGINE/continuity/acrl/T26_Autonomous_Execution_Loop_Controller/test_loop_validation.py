import pytest

from .loop_models import (
    LoopRequest,
)
from .loop_policy import (
    LoopPolicy,
)
from .loop_validation import (
    validate_request,
)


def make_request():
    return LoopRequest(
        loop_id="loop",
        execution_intent="run",
        checkpoint_id="checkpoint",
        checkpoint_fingerprint="a" * 64,
        continuity_recovery_id="recovery",
        continuity_fingerprint="b" * 64,
        evidence_resolution_id="resolution",
        evidence_fingerprint="c" * 64,
        max_iterations=5,
        max_retries_per_iteration=2,
        no_progress_limit=2,
        total_work_budget=10,
        total_token_budget=100,
        total_context_budget=100,
    )


def test_valid_request():
    validate_request(
        make_request(),
        LoopPolicy(),
    )


def test_zero_iterations_rejected():
    request = make_request()

    invalid = LoopRequest(
        loop_id=request.loop_id,
        execution_intent=request.execution_intent,
        checkpoint_id=request.checkpoint_id,
        checkpoint_fingerprint=request.checkpoint_fingerprint,
        continuity_recovery_id=request.continuity_recovery_id,
        continuity_fingerprint=request.continuity_fingerprint,
        evidence_resolution_id=request.evidence_resolution_id,
        evidence_fingerprint=request.evidence_fingerprint,
        max_iterations=0,
        max_retries_per_iteration=request.max_retries_per_iteration,
        no_progress_limit=request.no_progress_limit,
        total_work_budget=request.total_work_budget,
        total_token_budget=request.total_token_budget,
        total_context_budget=request.total_context_budget,
    )

    with pytest.raises(ValueError):
        validate_request(
            invalid,
            LoopPolicy(),
        )
