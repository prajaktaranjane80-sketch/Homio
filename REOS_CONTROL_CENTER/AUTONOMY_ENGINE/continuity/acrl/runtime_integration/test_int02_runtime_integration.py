from __future__ import annotations

from pathlib import Path

from .runtime_orchestrator import (
    ACRLRuntimeOrchestrator,
)
from .unified_runtime_context import (
    UnifiedRuntimeContext,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def build_context() -> UnifiedRuntimeContext:
    return UnifiedRuntimeContext.build(
        control_center_root=PROJECT_ROOT,
        mission_id="INT-02-ACRL-RUNTIME-INTEGRATION",
        objective="Bind existing ACRL T01-T30 runtime components.",
    )


def test_int02_binds_t21_to_t30() -> None:
    context = build_context()

    orchestrator = ACRLRuntimeOrchestrator(
        context
    )

    snapshot = orchestrator.build_snapshot()

    assert snapshot.healthy is True
    assert snapshot.registered_task_count == 30

    assert snapshot.bound_task_ids == (
        "T21",
        "T22",
        "T23",
        "T24",
        "T25",
        "T26",
        "T27",
        "T28",
        "T29",
        "T30",
    )

    assert len(snapshot.components) == 10


def test_int02_preserves_context_identity() -> None:
    context = build_context()

    snapshot = (
        ACRLRuntimeOrchestrator(
            context
        ).build_snapshot()
    )

    assert (
        snapshot.mission_id
        == "INT-02-ACRL-RUNTIME-INTEGRATION"
    )

    assert (
        snapshot.context_fingerprint
        == context.context_fingerprint
    )


def test_int02_does_not_mutate_runtime_context() -> None:
    context = build_context()
    before = context.to_dict()

    ACRLRuntimeOrchestrator(
        context
    ).build_snapshot()

    after = context.to_dict()

    assert after == before
