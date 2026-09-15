"""ACRL T08 — PART 08 Context Compression acceptance tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.checkpoint_engine import (
    CheckpointEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.context_compression import (
    CompressedContext,
    ContextCompressionAuthorityError,
    ContextCompressionEngine,
    ContextCompressionIntegrityError,
)
from AUTONOMY_ENGINE.continuity.acrl.dependency_authority_map import (
    build_dependency_authority_map,
)
from AUTONOMY_ENGINE.continuity.acrl.new_chat_bootstrap import (
    NewChatBootstrapEngine,
)


class Projection:
    """Minimal projection used for PART 08 acceptance tests."""

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
        checkpoint_id="CP-P08-001",
        created_at="2026-08-31T00:00:00+00:00",
    )


def make_bootstrap():
    engine = NewChatBootstrapEngine(
        project_dna=Projection(
            {
                "project": "HOMIO / REOS",
                "authority": "REOS_CONTROL_CENTER",
                "historical_chat_context": (
                    "OLD_SESSION_DATA_MUST_NOT_SURVIVE"
                ),
            }
        ),
        architecture_lock=Projection(
            {
                "status": "LOCKED",
                "source": "REOS_ARCHITECTURE",
                "relevant_architecture": [
                    "ACRL",
                    "REOS_CONTROL_CENTER",
                ],
                "historical_architecture": [
                    "OLD_ARCHITECTURE_DISCUSSION",
                ],
            }
        ),
        execution_state=Projection(
            {
                "current_gate": "CORE-005",
                "current_task": "CORE-005-T01",
                "current_subtask": "CORE-005-T01",
                "status": "CONTROL_CENTER_DRIVEN",
                "relevant_evidence": [
                    "T07_BOOTSTRAP_VALIDATED",
                ],
                "required_contracts": [
                    "REOS_CONTROL_CENTER_AUTHORITY",
                    "SAFE_AUTONOMOUS_RESUME",
                ],
                "resume_information": {
                    "checkpoint_id": "CP-P08-001",
                    "resume_mode": "SAFE_AUTONOMOUS_RESUME",
                },
                "historical_execution": [
                    "OLD_COMPLETED_SESSION",
                    "OBSOLETE_DEBUG_TRACE",
                ],
            }
        ),
        gate_continuity=Projection(
            {
                "current_gate": "CORE-005",
                "current_subtask": "CORE-005-T01",
                "historical_gate_context": [
                    "OLD_GATE_HISTORY",
                ],
            }
        ),
        dependency_map=build_dependency_authority_map(),
        checkpoint_engine=CheckpointEngine(),
    )

    return engine.build(
        bootstrap_id="BOOT-P08-001",
        checkpoint=make_checkpoint(),
    )


def make_compressed() -> CompressedContext:
    return ContextCompressionEngine.compress(
        make_bootstrap()
    )


def test_context_compression_output_is_machine_readable() -> None:
    context = make_compressed()

    payload = context.to_dict()

    assert isinstance(payload, dict)
    assert isinstance(payload["project_identity"], dict)
    assert isinstance(payload["architecture"], dict)
    assert isinstance(payload["execution"], dict)
    assert isinstance(payload["dependency_authority"], dict)
    assert isinstance(payload["checkpoint"], dict)


def test_current_task_is_retained() -> None:
    context = make_compressed()

    assert (
        context.execution["current_task"]
        == "CORE-005-T01"
    )


def test_relevant_architecture_is_retained() -> None:
    context = make_compressed()

    assert (
        context.architecture["relevant_architecture"]
        == [
            "ACRL",
            "REOS_CONTROL_CENTER",
        ]
    )


def test_required_dependencies_are_retained() -> None:
    context = make_compressed()

    assert context.dependency_authority
    assert (
        "dependency_authority"
        in context.preserved_sections
    )


def test_relevant_evidence_is_retained() -> None:
    context = make_compressed()

    assert (
        context.execution["relevant_evidence"]
        == [
            "T07_BOOTSTRAP_VALIDATED",
        ]
    )


def test_required_contracts_are_retained() -> None:
    context = make_compressed()

    assert (
        context.execution["required_contracts"]
        == [
            "REOS_CONTROL_CENTER_AUTHORITY",
            "SAFE_AUTONOMOUS_RESUME",
        ]
    )


def test_resume_information_is_retained() -> None:
    context = make_compressed()

    resume_information = (
        context.execution["resume_information"]
    )

    assert (
        resume_information["checkpoint_id"]
        == "CP-P08-001"
    )
    assert (
        resume_information["resume_mode"]
        == "SAFE_AUTONOMOUS_RESUME"
    )


def test_unnecessary_historical_context_is_removed() -> None:
    context = make_compressed()

    assert (
        "historical_chat_context"
        not in context.project_identity
    )

    assert (
        "historical_architecture"
        not in context.architecture
    )

    assert (
        "historical_execution"
        not in context.execution
    )

    assert (
        "historical_gate_context"
        not in context.gate_continuity
    )


def test_authoritative_meaning_is_preserved() -> None:
    context = make_compressed()

    assert (
        context.authority
        == "REOS_CONTROL_CENTER"
    )

    assert (
        context.architecture["status"]
        == "LOCKED"
    )

    assert (
        context.execution["current_gate"]
        == "CORE-005"
    )

    assert (
        context.execution["current_subtask"]
        == "CORE-005-T01"
    )

    assert (
        context.resume_mode
        == "SAFE_AUTONOMOUS_RESUME"
    )


def test_compressed_context_remains_resumable() -> None:
    context = make_compressed()

    ContextCompressionEngine.validate_for_resume(
        context
    )

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


def test_compression_remains_deterministic() -> None:
    first = make_compressed()
    second = make_compressed()

    assert (
        first.fingerprint
        == second.fingerprint
    )


def test_tampered_compressed_context_fails_closed() -> None:
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


def test_missing_authoritative_section_fails_closed() -> None:
    context = make_compressed()

    object.__setattr__(
        context,
        "dependency_authority",
        {},
    )

    with pytest.raises(
        ContextCompressionIntegrityError
    ):
        ContextCompressionEngine.validate_for_resume(
            context
        )


def test_unsafe_resume_mode_fails_closed() -> None:
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
