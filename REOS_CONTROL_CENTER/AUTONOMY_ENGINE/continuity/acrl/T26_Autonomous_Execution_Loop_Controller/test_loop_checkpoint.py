from dataclasses import dataclass

from .loop_checkpoint import (
    validate_checkpoint_binding,
)
from .loop_models import (
    ExecutionLoop,
    LoopStatus,
)


@dataclass
class Decision:
    value: str


@dataclass
class Checkpoint:
    checkpoint_id: str
    checkpoint_fingerprint: str


@dataclass
class Result:
    decision: Decision
    checkpoint: Checkpoint


def test_checkpoint_binding():
    loop = ExecutionLoop(
        schema_version="1.0",
        loop_version="1.0",
        loop_id="loop",
        status=LoopStatus.CREATED,
        execution_intent="run",
        checkpoint_id="checkpoint",
        checkpoint_fingerprint="a" * 64,
        continuity_recovery_id="recovery",
        continuity_fingerprint="b" * 64,
        evidence_resolution_id="resolution",
        evidence_fingerprint="c" * 64,
        max_iterations=5,
        max_retries_per_iteration=2,
        current_iteration=0,
        total_work_budget=10,
        total_token_budget=100,
        total_context_budget=100,
        work_consumed=0,
        token_consumed=0,
        context_consumed=0,
        no_progress_limit=2,
        no_progress_count=0,
        iterations=(),
        terminal_reason=None,
        loop_fingerprint="d" * 64,
    )

    result = Result(
        decision=Decision(
            "CHECKPOINT_CREATED"
        ),
        checkpoint=Checkpoint(
            checkpoint_id="checkpoint",
            checkpoint_fingerprint="a" * 64,
        ),
    )

    validate_checkpoint_binding(
        loop,
        result,
    )
