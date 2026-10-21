from ._t23_test_support import build_t23_source_store
from .continuity_coordinator import recover_continuity
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)
from .continuity_store import ContinuityStore


def make_request():
    return ContinuityRequest(
        recovery_id="recovery-1",
        project_id="HOMIO",
        source_resolution_id="resolution-1",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=("project", "state"),
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
            source_layer="T09",
            source_name="StateSnapshot",
            status=ContinuityStatus.CURRENT,
            content_fingerprint="e" * 64,
            sequence=2,
            canonical=True,
        ),
    )


def make_context():
    return {
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
        "provenance": {
            "authority": "REOS_CONTROL_CENTER",
            "state_path": "REOS_CONTROL_CENTER/data/state.json",
            "project_fingerprint_source_layer": "T03",
            "state_fingerprint_source_layer": "T09",
            "branch_source_layer": "T21",
            "commit_sha_source_layer": "T21",
            "source_resolution_id": "resolution-1",
            "evidence_ids": ["project", "state"],
        },
    }


def test_continuity_is_recovered():
    request = make_request()
    evidence = make_evidence()
    source_resolution_store = build_t23_source_store(
        request,
        evidence,
    )

    result = recover_continuity(
        request=request,
        evidence_items=evidence,
        store=ContinuityStore(),
        project_context=make_context(),
        source_resolution_store=source_resolution_store,
    )

    assert result.decision is ContinuityDecision.RECOVERED
    assert result.snapshot is not None
    assert result.snapshot.project_id == "HOMIO"
    assert tuple(
        item.evidence_id for item in result.selected_evidence
    ) == ("project", "state")
