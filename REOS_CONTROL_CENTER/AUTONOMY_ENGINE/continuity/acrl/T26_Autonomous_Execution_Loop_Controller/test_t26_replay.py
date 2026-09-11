from .loop_controller import (
    start_execution_loop,
)
from .loop_models import (
    LoopDecision,
    LoopRequest,
)
from .loop_store import (
    LoopStore,
)


class Decision:
    value = "CHECKPOINT_CREATED"


class Checkpoint:
    checkpoint_id = "checkpoint"
    checkpoint_fingerprint = "a" * 64


class CheckpointResult:
    decision = Decision()
    checkpoint = Checkpoint()


class Result:
    def __init__(self, value):
        self.decision = type(
            "Decision",
            (),
            {"value": value},
        )()


def make_request():
    return LoopRequest(
        loop_id="same",
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


def test_replay_detected():
    store = LoopStore()

    first = start_execution_loop(
        request=make_request(),
        store=store,
        checkpoint_result=CheckpointResult(),
        continuity_result=Result(
            "RECOVERED"
        ),
        evidence_result=Result(
            "RESOLVED"
        ),
        budget_result=Result(
            "ALLOCATED"
        ),
    )

    second = start_execution_loop(
        request=make_request(),
        store=store,
        checkpoint_result=CheckpointResult(),
        continuity_result=Result(
            "RECOVERED"
        ),
        evidence_result=Result(
            "RESOLVED"
        ),
        budget_result=Result(
            "ALLOCATED"
        ),
    )

    assert (
        first.decision
        is LoopDecision.STARTED
    )

    assert (
        second.decision
        is LoopDecision.REPLAY_DETECTED
    )
