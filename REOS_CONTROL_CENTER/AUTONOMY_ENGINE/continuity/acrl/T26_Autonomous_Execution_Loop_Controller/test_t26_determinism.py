from .loop_controller import (
    start_execution_loop,
)
from .loop_models import (
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


class Continuity:
    decision = type(
        "Decision",
        (),
        {"value": "RECOVERED"},
    )()


class Evidence:
    decision = type(
        "Decision",
        (),
        {"value": "RESOLVED"},
    )()


class Budget:
    decision = type(
        "Decision",
        (),
        {"value": "ALLOCATED"},
    )()


def make_request():
    return LoopRequest(
        loop_id="deterministic",
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


def run():
    return start_execution_loop(
        request=make_request(),
        store=LoopStore(),
        checkpoint_result=CheckpointResult(),
        continuity_result=Continuity(),
        evidence_result=Evidence(),
        budget_result=Budget(),
    )


def test_same_input_same_identity():
    first = run()
    second = run()

    assert (
        first.result_fingerprint
        == second.result_fingerprint
    )
