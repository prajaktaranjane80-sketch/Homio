from .continuity_coordinator import (
    recover_continuity,
)
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)
from .continuity_store import (
    ContinuityStore,
)


def make_request():
    return ContinuityRequest(
        recovery_id="recovery-1",
        project_id="HOMIO",
        source_resolution_id="resolution-1",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=(
            "project",
            "state",
        ),
        recovery_nonce="nonce",
    )


def make_evidence():
    return (
        ContinuityEvidence(
            evidence_id="project",
            subject="project",
            source_layer="T03",
            source_name="ProjectDNA",
            status=ContinuityStatus.CURRENT,
            content_fingerprint="d" * 64,
            sequence=1,
            canonical=True,
        ),
        ContinuityEvidence(
            evidence_id="state",
            subject="state",
            source_layer="T03",
            source_name="StateSnapshot",
            status=ContinuityStatus.CURRENT,
            content_fingerprint="e" * 64,
            sequence=2,
            canonical=True,
        ),
    )


def test_continuity_is_recovered():
    result = recover_continuity(
        request=make_request(),
        evidence_items=make_evidence(),
        store=ContinuityStore(),
        project_context={
            "project_fingerprint": "a" * 64,
            "state_fingerprint": "b" * 64,
            "branch": "reos-development",
            "commit_sha": "c" * 40,
            "phase": "PRE-CODING ARCHITECTURE",
            "gate_id": "T24",
            "gate_status": "CURRENT",
            "current_task": "T24",
            "current_subtask": "T24-01",
            "current_subtask_status": "READY",
        },
    )

    assert (
        result.decision
        is ContinuityDecision.RECOVERED
    )

    assert result.snapshot is not None
    assert (
        result.snapshot.project_id
        == "HOMIO"
    )
