from __future__ import annotations

from .continuity_identity import fingerprint
from .continuity_models import (
    ContinuityRequest,
    ContinuitySnapshot,
)


def build_snapshot(
    *,
    request: ContinuityRequest,
    project_id: str,
    project_fingerprint: str,
    state_fingerprint: str,
    branch: str,
    commit_sha: str,
    phase: str,
    gate_id: str,
    gate_status: str,
    current_task: str,
    current_subtask: str,
    current_subtask_status: str,
    completed_subtasks: tuple[str, ...],
    pending_subtasks: tuple[str, ...],
    evidence_fingerprints: tuple[str, ...],
    execution_checkpoint_id: str | None,
    execution_checkpoint_fingerprint: str | None,
) -> ContinuitySnapshot:
    payload = {
        "schema_version": "1.0",
        "continuity_version": "1.0",
        "project_id": project_id,
        "project_fingerprint": project_fingerprint,
        "state_fingerprint": state_fingerprint,
        "branch": branch,
        "commit_sha": commit_sha,
        "phase": phase,
        "gate_id": gate_id,
        "gate_status": gate_status,
        "current_task": current_task,
        "current_subtask": current_subtask,
        "current_subtask_status": current_subtask_status,
        "completed_subtasks": list(
            completed_subtasks
        ),
        "pending_subtasks": list(
            pending_subtasks
        ),
        "execution_checkpoint_id": (
            execution_checkpoint_id
        ),
        "execution_checkpoint_fingerprint": (
            execution_checkpoint_fingerprint
        ),
        "evidence_fingerprints": list(
            evidence_fingerprints
        ),
        "source_resolution_id": (
            request.source_resolution_id
        ),
    }

    return ContinuitySnapshot(
        schema_version="1.0",
        continuity_version="1.0",
        project_id=project_id,
        project_fingerprint=project_fingerprint,
        state_fingerprint=state_fingerprint,
        branch=branch,
        commit_sha=commit_sha,
        phase=phase,
        gate_id=gate_id,
        gate_status=gate_status,
        current_task=current_task,
        current_subtask=current_subtask,
        current_subtask_status=current_subtask_status,
        completed_subtasks=completed_subtasks,
        pending_subtasks=pending_subtasks,
        execution_checkpoint_id=(
            execution_checkpoint_id
        ),
        execution_checkpoint_fingerprint=(
            execution_checkpoint_fingerprint
        ),
        evidence_fingerprints=(
            evidence_fingerprints
        ),
        source_resolution_id=(
            request.source_resolution_id
        ),
        recovery_fingerprint=fingerprint(
            payload
        ),
    )
