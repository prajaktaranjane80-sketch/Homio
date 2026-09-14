"""ACRL T06 — Checkpoint Continuity acceptance tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .checkpoint_continuity import (
    CheckpointContinuityConflictError,
    CheckpointContinuityIntegrityError,
    CheckpointContinuityReader,
    CheckpointContinuityStatus,
)


def _write_state(
    root: Path,
    *,
    checkpoints: list[dict],
    current_gate: str = "CORE-005",
    current_task: str = "CORE-005-T01",
) -> None:
    data = root / "data"
    data.mkdir(parents=True)

    state = {
        "meta": {
            "schema_version": 3,
            "control_center_version": "6.0",
        },
        "constitution": {
            "canonical_source": "data/state.json",
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
        "execution": {
            "current_gate": current_gate,
            "current_task": current_task,
        },
        "checkpoints": checkpoints,
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def _checkpoint(
    *,
    checkpoint_id: str,
    created_at: str,
    gate: str = "CORE-005",
    task: str = "CORE-005-T01",
    subtask: str = "CORE-005-T01",
    evidence_verified: bool = True,
    evidence_ids: list[str] | None = None,
    resumable: bool = True,
) -> dict:
    return {
        "checkpoint_id": checkpoint_id,
        "created_at": created_at,
        "scope": {
            "phase": "PRE-CODING ARCHITECTURE",
            "gate": gate,
            "task": task,
            "subtask": subtask,
        },
        "evidence": {
            "verified": evidence_verified,
            "evidence_ids": evidence_ids or ["EV-001"],
        },
        "interruption_boundary": {
            "type": "SAFE_INTERRUPTION",
            "resumable": resumable,
            "reason": "Execution safely checkpointed.",
        },
    }


def test_latest_checkpoint_is_selected(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-001",
                created_at="2026-09-01T10:00:00+00:00",
            ),
            _checkpoint(
                checkpoint_id="CP-002",
                created_at="2026-09-02T10:00:00+00:00",
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.checkpoint_id == "CP-002"


def test_checkpoint_identity_is_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-IDENTITY",
                created_at="2026-09-02T10:00:00+00:00",
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.checkpoint_id == "CP-IDENTITY"
    assert len(continuity.checkpoint_fingerprint) == 64


def test_checkpoint_scope_is_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-SCOPE",
                created_at="2026-09-02T10:00:00+00:00",
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.scope.phase == "PRE-CODING ARCHITECTURE"
    assert continuity.scope.gate_id == "CORE-005"
    assert continuity.scope.task_id == "CORE-005-T01"
    assert continuity.scope.subtask_id == "CORE-005-T01"


def test_completion_evidence_is_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-EVIDENCE",
                created_at="2026-09-02T10:00:00+00:00",
                evidence_ids=[
                    "EV-001",
                    "EV-002",
                ],
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.completion_evidence.verified is True
    assert continuity.completion_evidence.evidence_ids == (
        "EV-001",
        "EV-002",
    )
    assert continuity.completion_evidence.evidence_count == 2


def test_resumable_position_is_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-RESUME",
                created_at="2026-09-02T10:00:00+00:00",
                subtask="CORE-005-T03",
            ),
        ],
        current_task="CORE-005-T01",
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert (
        continuity.resumable_position
        == "CORE-005:CORE-005-T01:CORE-005-T03"
    )


def test_interruption_boundary_is_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-BOUNDARY",
                created_at="2026-09-02T10:00:00+00:00",
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert (
        continuity.interruption_boundary.boundary_type
        == "SAFE_INTERRUPTION"
    )
    assert (
        continuity.interruption_boundary.resumable
        is True
    )


def test_valid_checkpoint_is_resumable(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-VALID",
                created_at="2026-09-02T10:00:00+00:00",
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.status == (
        CheckpointContinuityStatus.RESUMABLE
    )
    assert continuity.can_resume() is True


def test_unverified_checkpoint_is_blocked(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-BLOCK-EVIDENCE",
                created_at="2026-09-02T10:00:00+00:00",
                evidence_verified=False,
                evidence_ids=[],
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.status == (
        CheckpointContinuityStatus.BLOCKED
    )
    assert continuity.can_resume() is False


def test_non_resumable_boundary_is_blocked(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-BLOCK-BOUNDARY",
                created_at="2026-09-02T10:00:00+00:00",
                resumable=False,
            ),
        ],
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.status == (
        CheckpointContinuityStatus.BLOCKED
    )


def test_checkpoint_gate_conflict_is_blocked(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-CONFLICT",
                created_at="2026-09-02T10:00:00+00:00",
                gate="CORE-004",
            ),
        ],
        current_gate="CORE-005",
    )

    continuity = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.status == (
        CheckpointContinuityStatus.BLOCKED
    )


def test_verified_checkpoint_requires_evidence(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-NO-EVIDENCE",
                created_at="2026-09-02T10:00:00+00:00",
                evidence_verified=True,
                evidence_ids=[],
            ),
        ],
    )

    with pytest.raises(
        CheckpointContinuityIntegrityError
    ):
        CheckpointContinuityReader(tmp_path).reconstruct()


def test_missing_checkpoint_is_blocked(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[],
    )

    with pytest.raises(
        CheckpointContinuityConflictError
    ):
        CheckpointContinuityReader(tmp_path).reconstruct()


def test_projection_is_serializable(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        checkpoints=[
            _checkpoint(
                checkpoint_id="CP-SERIAL",
                created_at="2026-09-02T10:00:00+00:00",
            ),
        ],
    )

    payload = (
        CheckpointContinuityReader(tmp_path)
        .reconstruct()
        .to_dict()
    )

    assert payload["schema_version"] == "1.0"
    assert payload["checkpoint"]["id"] == "CP-SERIAL"
    assert (
        payload["resolution"]["status"]
        == "RESUMABLE"
    )
    assert len(
        payload["authority"]["source_state_sha256"]
    ) == 64
