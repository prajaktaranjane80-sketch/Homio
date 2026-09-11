from .continuity_models import (
    ContinuityRequest,
)
from .continuity_snapshot import (
    build_snapshot,
)


def test_snapshot_fingerprint_exists():
    request = ContinuityRequest(
        recovery_id="r",
        project_id="HOMIO",
        source_resolution_id="resolution",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=("ev",),
        recovery_nonce="nonce",
    )

    snapshot = build_snapshot(
        request=request,
        project_id="HOMIO",
        project_fingerprint="a" * 64,
        state_fingerprint="b" * 64,
        branch="reos-development",
        commit_sha="c" * 40,
        phase="PRE-CODING ARCHITECTURE",
        gate_id="T24",
        gate_status="CURRENT",
        current_task="T24",
        current_subtask="T24-01",
        current_subtask_status="READY",
        completed_subtasks=(),
        pending_subtasks=("T24-01",),
        evidence_fingerprints=("d" * 64,),
        execution_checkpoint_id=None,
        execution_checkpoint_fingerprint=None,
    )

    assert len(
        snapshot.recovery_fingerprint
    ) == 64

    assert (
        snapshot.commit_sha
        == "c" * 40
    )
