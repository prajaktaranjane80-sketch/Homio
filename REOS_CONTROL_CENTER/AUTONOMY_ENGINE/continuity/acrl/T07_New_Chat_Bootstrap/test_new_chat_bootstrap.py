"""ACRL T07 — New-Chat Bootstrap / Handoff tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.new_chat_bootstrap import (
    BootstrapAuthorityError,
    BootstrapContext,
    BootstrapIntegrityError,
    BootstrapValidationError,
    NewChatBootstrapEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.checkpoint_engine import (
    CheckpointEngine,
    ExecutionCheckpoint,
)
from AUTONOMY_ENGINE.continuity.acrl.dependency_authority_map import (
    build_dependency_authority_map,
)


class Projection:
    """Minimal test projection compatible with T07."""

    def __init__(
        self,
        data: dict[str, object],
    ) -> None:
        self.data = data

    def to_dict(self) -> dict[str, object]:
        return dict(self.data)


def make_checkpoint() -> ExecutionCheckpoint:
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "PRE-CODING ARCHITECTURE",
            "current_gate": "CORE-005",
            "current_subtask": "CORE-005-T01",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        checkpoint_id="CP-T07-001",
        created_at="2026-08-31T00:00:00+00:00",
    )


def make_engine() -> NewChatBootstrapEngine:
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
                "current_gate": "CORE-005",
                "current_subtask": "CORE-005-T01",
                "status": "CONTROL_CENTER_DRIVEN",
            }
        ),
        gate_continuity=Projection(
            {
                "current_gate": "CORE-005",
                "current_subtask": "CORE-005-T01",
            }
        ),
        dependency_map=build_dependency_authority_map(),
        checkpoint_engine=CheckpointEngine(),
    )


def test_bootstrap_is_created() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-001",
        checkpoint=make_checkpoint(),
    )

    assert isinstance(
        context,
        BootstrapContext,
    )


def test_bootstrap_authority_is_reos() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-002",
        checkpoint=make_checkpoint(),
    )

    assert (
        context.authority
        == "REOS_CONTROL_CENTER"
    )


def test_bootstrap_contains_checkpoint() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-003",
        checkpoint=make_checkpoint(),
    )

    assert (
        context.checkpoint["checkpoint_id"]
        == "CP-T07-001"
    )


def test_bootstrap_integrity_is_valid() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-004",
        checkpoint=make_checkpoint(),
    )

    assert context.verify_integrity() is True


def test_resume_validation_passes() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-005",
        checkpoint=make_checkpoint(),
    )

    NewChatBootstrapEngine.validate_for_resume(
        context
    )


def test_safe_resume_mode_is_set() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-006",
        checkpoint=make_checkpoint(),
    )

    assert (
        context.resume_mode
        == "SAFE_AUTONOMOUS_RESUME"
    )


def test_resume_summary_reconstructs_position() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-007",
        checkpoint=make_checkpoint(),
    )

    summary = NewChatBootstrapEngine.resume_summary(
        context
    )

    assert summary["current_gate"] == "CORE-005"
    assert (
        summary["current_subtask"]
        == "CORE-005-T01"
    )


def test_empty_bootstrap_id_is_rejected() -> None:
    with pytest.raises(
        BootstrapValidationError
    ):
        make_engine().build(
            bootstrap_id="",
            checkpoint=make_checkpoint(),
        )


def test_tampered_checkpoint_is_rejected() -> None:
    checkpoint = make_checkpoint()

    object.__setattr__(
        checkpoint,
        "state_fingerprint",
        "tampered",
    )

    with pytest.raises(
        BootstrapIntegrityError
    ):
        make_engine().build(
            bootstrap_id="BOOT-008",
            checkpoint=checkpoint,
        )


def test_tampered_bootstrap_is_rejected() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-009",
        checkpoint=make_checkpoint(),
    )

    object.__setattr__(
        context,
        "fingerprint",
        "tampered",
    )

    with pytest.raises(
        BootstrapIntegrityError
    ):
        NewChatBootstrapEngine.validate_for_resume(
            context
        )


def test_wrong_authority_is_rejected() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-010",
        checkpoint=make_checkpoint(),
    )

    original_fingerprint = context.fingerprint

    object.__setattr__(
        context,
        "authority",
        "CHAT_CONTEXT",
    )

    # The authority mutation must make the fingerprint invalid.
    assert (
        context.fingerprint
        == original_fingerprint
    )

    with pytest.raises(
        BootstrapIntegrityError
    ):
        NewChatBootstrapEngine.validate_for_resume(
            context
        )


def test_unlocked_architecture_is_rejected() -> None:
    engine = make_engine()

    engine.architecture_lock = Projection(
        {
            "status": "UNLOCKED",
        }
    )

    with pytest.raises(
        BootstrapAuthorityError
    ):
        engine.build(
            bootstrap_id="BOOT-011",
            checkpoint=make_checkpoint(),
        )


def test_missing_gate_is_rejected_on_resume() -> None:
    engine = make_engine()

    engine.execution_state = Projection(
        {
            "status": "CONTROL_CENTER_DRIVEN",
        }
    )

    engine.gate_continuity = Projection(
        {
            "status": "UNKNOWN",
        }
    )

    context = engine.build(
        bootstrap_id="BOOT-012",
        checkpoint=make_checkpoint(),
    )

    with pytest.raises(
        BootstrapAuthorityError
    ):
        NewChatBootstrapEngine.resume_summary(
            context
        )


def test_missing_subtask_is_rejected_on_resume() -> None:
    engine = make_engine()

    engine.execution_state = Projection(
        {
            "current_gate": "CORE-005",
        }
    )

    engine.gate_continuity = Projection(
        {
            "current_gate": "CORE-005",
        }
    )

    context = engine.build(
        bootstrap_id="BOOT-013",
        checkpoint=make_checkpoint(),
    )

    with pytest.raises(
        BootstrapAuthorityError
    ):
        NewChatBootstrapEngine.resume_summary(
            context
        )


def test_bootstrap_payload_is_machine_readable() -> None:
    context = make_engine().build(
        bootstrap_id="BOOT-014",
        checkpoint=make_checkpoint(),
    )

    payload = context.to_dict()

    assert payload["schema_version"] == "1.0"
    assert payload["authority"] == "REOS_CONTROL_CENTER"
    assert isinstance(
        payload["checkpoint"],
        dict,
    )


def test_bootstrap_fingerprint_is_deterministic() -> None:
    first = make_engine().build(
        bootstrap_id="BOOT-015",
        checkpoint=make_checkpoint(),
    )

    second = make_engine().build(
        bootstrap_id="BOOT-015",
        checkpoint=make_checkpoint(),
    )

    assert (
        first.fingerprint
        == second.fingerprint
    )