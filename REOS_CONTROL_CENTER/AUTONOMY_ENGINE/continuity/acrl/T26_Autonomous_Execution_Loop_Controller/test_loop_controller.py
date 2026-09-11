from dataclasses import dataclass
from enum import Enum

from .loop_controller import (
    advance_execution_loop,
    start_execution_loop,
)
from .loop_models import (
    LoopDecision,
    LoopRequest,
)
from .loop_store import (
    LoopStore,
)


class Decision(Enum):
    CHECKPOINT_CREATED = (
        "CHECKPOINT_CREATED"
    )


class ContinuityDecision(Enum):
    RECOVERED = "RECOVERED"


class EvidenceDecision(Enum):
    RESOLVED = "RESOLVED"


class BudgetDecision(Enum):
    ALLOCATED = "ALLOCATED"


@dataclass
class Checkpoint:
    checkpoint_id: str
    checkpoint_fingerprint: str


@dataclass
class CheckpointResult:
    decision: Decision
    checkpoint: Checkpoint


@dataclass
class Result:
    decision: object


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


def test_loop_starts():
    store = LoopStore()

    result = start_execution_loop(
        request=make_request(),
        store=store,
        checkpoint_result=CheckpointResult(
            decision=Decision.CHECKPOINT_CREATED,
            checkpoint=Checkpoint(
                checkpoint_id="checkpoint",
                checkpoint_fingerprint="a" * 64,
            ),
        ),
        continuity_result=Result(
            decision=ContinuityDecision.RECOVERED
        ),
        evidence_result=Result(
            decision=EvidenceDecision.RESOLVED
        ),
        budget_result=Result(
            decision=BudgetDecision.ALLOCATED
        ),
    )

    assert (
        result.decision
        is LoopDecision.STARTED
    )

    assert result.loop is not None


def test_loop_iteration_advances():
    store = LoopStore()

    result = start_execution_loop(
        request=make_request(),
        store=store,
        checkpoint_result=CheckpointResult(
            decision=Decision.CHECKPOINT_CREATED,
            checkpoint=Checkpoint(
                checkpoint_id="checkpoint",
                checkpoint_fingerprint="a" * 64,
            ),
        ),
        continuity_result=Result(
            decision=ContinuityDecision.RECOVERED
        ),
        evidence_result=Result(
            decision=EvidenceDecision.RESOLVED
        ),
        budget_result=Result(
            decision=BudgetDecision.ALLOCATED
        ),
    )

    advanced = advance_execution_loop(
        loop=result.loop,
        store=store,
        progress_fingerprint="p1",
        work_consumed=1,
        token_consumed=10,
        context_consumed=5,
    )

    assert advanced.loop.current_iteration == 1
    assert (
        advanced.decision
        is LoopDecision.CONTINUE
    )
