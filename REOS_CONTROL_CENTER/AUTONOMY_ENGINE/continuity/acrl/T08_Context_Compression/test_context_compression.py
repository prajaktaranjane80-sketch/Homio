"""ACRL T08 — Context Compression tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.checkpoint_engine import (
    CheckpointEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.context_compression import (
    CompressedContext,
    ContextCompressionAuthorityError,
    ContextCompressionEngine,
    ContextCompressionError,
    ContextCompressionIntegrityError,
    ContextCompressionValidationError,
)
from AUTONOMY_ENGINE.continuity.acrl.dependency_authority_map import (
    build_dependency_authority_map,
)
from AUTONOMY_ENGINE.continuity.acrl.new_chat_bootstrap import (
    NewChatBootstrapEngine,
)


class Projection:
    """Minimal read-only projection used by T08 tests."""

    def __init__(
        self,
        data: dict[str, object],
    ) -> None:
        self.data = data

    def to_dict(self) -> dict[str, object]:
        return dict(self.data)


def make_checkpoint():
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "PRE-CODING ARCHITECTURE",
            "current_gate": "CORE-005",
            "current_subtask": "CORE-005-T01",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        checkpoint_id="CP-T08-001",
        created_at="2026-08-31T00:00:00+00:00",
    )


def make_bootstrap():
    engine = NewChatBootstrapEngine(
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

    return engine.build(
        bootstrap_id="BOOT-T08-001",
        checkpoint=make_checkpoint(),
    )


def make_compressed():
    return ContextCompressionEngine.compress(
        make_bootstrap()
    )


def test_context_is_compressed() -> None:
    context = make_compressed()

    assert isinstance(
        context,
        CompressedContext,
    )


def test_authority_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.authority
        == "REOS_CONTROL_CENTER"
    )


def test_project_identity_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.project_identity["project"]
        == "HOMIO / REOS"
    )


def test_architecture_lock_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.architecture["status"]
        == "LOCKED"
    )


def test_execution_state_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.execution["current_gate"]
        == "CORE-005"
    )

    assert (
        context.execution["current_subtask"]
        == "CORE-005-T01"
    )


def test_gate_continuity_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.gate_continuity["current_gate"]
        == "CORE-005"
    )


def test_dependency_authority_is_preserved() -> None:
    context = make_compressed()

    assert isinstance(
        context.dependency_authority,
        dict,
    )


def test_checkpoint_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.checkpoint["checkpoint_id"]
        == "CP-T08-001"
    )


def test_resume_mode_is_safe() -> None:
    context = make_compressed()

    assert (
        context.resume_mode
        == "SAFE_AUTONOMOUS_RESUME"
    )


def test_required_sections_are_recorded() -> None:
    context = make_compressed()

    assert set(
        ContextCompressionEngine.REQUIRED_SECTIONS
    ).issubset(
        set(context.preserved_sections)
    )


def test_compressed_context_integrity_passes() -> None:
    context = make_compressed()

    assert (
        context.verify_integrity()
        is True
    )


def test_resume_validation_passes() -> None:
    context = make_compressed()

    ContextCompressionEngine.validate_for_resume(
        context
    )


def test_resume_summary_reconstructs_position() -> None:
    context = make_compressed()

    summary = (
        ContextCompressionEngine.resume_summary(
            context
        )
    )

    assert (
        summary["current_gate"]
        == "CORE-005"
    )

    assert (
        summary["current_subtask"]
        == "CORE-005-T01"
    )


def test_tampered_compressed_context_is_rejected() -> None:
    context = make_compressed()

    object.__setattr__(
        context,
        "fingerprint",
        "tampered",
    )

    with pytest.raises(
        ContextCompressionIntegrityError
    ):
        ContextCompressionEngine.validate_for_resume(
            context
        )


def test_missing_required_section_is_rejected() -> None:
    context = make_compressed()

    object.__setattr__(
        context,
        "checkpoint",
        {},
    )

    with pytest.raises(
        ContextCompressionIntegrityError
    ):
        ContextCompressionEngine.validate_for_resume(
            context
        )


def test_unsafe_resume_mode_is_rejected() -> None:
    context = make_compressed()

    object.__setattr__(
        context,
        "resume_mode",
        "UNSAFE",
    )

    with pytest.raises(
        ContextCompressionIntegrityError
    ):
        ContextCompressionEngine.validate_for_resume(
            context
        )


def test_non_bootstrap_input_is_rejected() -> None:
    with pytest.raises(
        ContextCompressionValidationError
    ):
        ContextCompressionEngine.compress(
            object()
        )


def test_compression_is_deterministic() -> None:
    first = make_compressed()
    second = make_compressed()

    assert (
        first.fingerprint
        == second.fingerprint
    )


def test_source_bootstrap_identity_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.source_bootstrap_id
        == "BOOT-T08-001"
    )


def test_compression_version_is_present() -> None:
    context = make_compressed()

    assert (
        context.compression_version
        == "T08-1.0"
    ) 