from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T06_Checkpoint_Engine.checkpoint_engine import (
    CheckpointEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.T07_New_Chat_Bootstrap.new_chat_bootstrap import (
    BootstrapAuthorityError,
    NewChatBootstrapEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.dependency_authority_map import (
    build_dependency_authority_map,
)


class Projection:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data

    def to_dict(self) -> dict[str, object]:
        return dict(self.data)


GATE = "CORE-005"
SUBTASK = "CORE-005-T01"
STATUS = "CONTROL_CENTER_DRIVEN"


def make_checkpoint(
    *,
    gate: str = GATE,
    subtask: str = SUBTASK,
    status: str = STATUS,
):
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "TEST_PHASE",
            "current_gate": gate,
            "current_subtask": subtask,
            "status": status,
        },
        checkpoint_id="CP-T07-COHERENCE-001",
        created_at="2026-10-21T10:00:00+00:00",
    )


def make_engine(
    *,
    current_gate: str = GATE,
    current_task: str = SUBTASK,
    current_subtask: str = SUBTASK,
    current_subtask_status: str = STATUS,
    continuity_gate: str | None = None,
    continuity_subtask: str | None = None,
) -> NewChatBootstrapEngine:
    return NewChatBootstrapEngine(
        project_dna=Projection(
            {
                "project": "HOMIO / REOS",
                "authority": "REOS_CONTROL_CENTER",
            }
        ),
        architecture_lock=Projection(
            {
                "status": "LOCKED",
                "source": "REOS_ARCHITECTURE",
            }
        ),
        execution_state=Projection(
            {
                "current_gate": current_gate,
                "current_task": current_task,
                "current_subtask": current_subtask,
                "current_subtask_status": current_subtask_status,
            }
        ),
        gate_continuity=Projection(
            {
                "current_gate": (
                    current_gate
                    if continuity_gate is None
                    else continuity_gate
                ),
                "current_subtask": (
                    current_subtask
                    if continuity_subtask is None
                    else continuity_subtask
                ),
            }
        ),
        dependency_map=build_dependency_authority_map(),
        checkpoint_engine=CheckpointEngine(),
    )


def build(engine: NewChatBootstrapEngine, checkpoint):
    return engine.build(
        bootstrap_id="BOOT-T07-COHERENCE",
        checkpoint=checkpoint,
    )


def test_matching_checkpoint_and_authoritative_context_are_accepted():
    context = build(make_engine(), make_checkpoint())

    NewChatBootstrapEngine.validate_for_resume(context)

    assert context.restart_payload["current_gate"] == GATE
    assert context.restart_payload["current_subtask"] == SUBTASK


def test_stale_checkpoint_gate_is_rejected():
    checkpoint = make_checkpoint(gate="CORE-006")

    with pytest.raises(
        BootstrapAuthorityError,
        match="current_gate",
    ):
        build(make_engine(), checkpoint)


def test_stale_checkpoint_subtask_is_rejected():
    checkpoint = make_checkpoint(subtask="CORE-005-T02")

    with pytest.raises(
        BootstrapAuthorityError,
        match="current_subtask",
    ):
        build(make_engine(), checkpoint)


def test_execution_task_must_bind_to_checkpoint_subtask():
    engine = make_engine(
        current_task="CORE-005-T02",
        current_subtask="CORE-005-T01",
    )

    with pytest.raises(
        BootstrapAuthorityError,
        match="bind current_task",
    ):
        build(engine, make_checkpoint())


def test_checkpoint_status_must_match_execution_status():
    checkpoint = make_checkpoint(status="UNKNOWN")

    with pytest.raises(
        BootstrapAuthorityError,
        match="status",
    ):
        build(make_engine(), checkpoint)


def test_conflicting_gate_continuity_is_rejected():
    engine = make_engine(continuity_gate="CORE-006")

    with pytest.raises(
        BootstrapAuthorityError,
        match="Gate-continuity current_gate",
    ):
        build(engine, make_checkpoint())


def test_conflicting_subtask_continuity_is_rejected():
    engine = make_engine(continuity_subtask="CORE-005-T02")

    with pytest.raises(
        BootstrapAuthorityError,
        match="Gate-continuity current_subtask",
    ):
        build(engine, make_checkpoint())


def test_noncanonical_checkpoint_source_is_rejected():
    class UntrustedCheckpoint:
        def verify_integrity(self) -> bool:
            return True

        def to_dict(self) -> dict[str, object]:
            return {
                "checkpoint_id": "CP-UNTRUSTED",
                "source": "CHAT_CONTEXT",
                "state_snapshot": {
                    "phase": "TEST_PHASE",
                    "current_gate": GATE,
                    "current_subtask": SUBTASK,
                    "status": STATUS,
                },
            }

    with pytest.raises(
        BootstrapAuthorityError,
        match="canonical REOS state authority",
    ):
        build(make_engine(), UntrustedCheckpoint())
