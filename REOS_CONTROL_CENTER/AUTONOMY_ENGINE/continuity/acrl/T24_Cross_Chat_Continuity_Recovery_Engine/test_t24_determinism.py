from .continuity_coordinator import (
    recover_continuity,
)
from .continuity_models import (
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)
from .continuity_store import (
    ContinuityStore,
)


def make_request():
    return ContinuityRequest(
        recovery_id="deterministic",
        project_id="HOMIO",
        source_resolution_id="resolution",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=("ev",),
        recovery_nonce="nonce",
    )


def make_evidence():
    return (
        ContinuityEvidence(
            evidence_id="ev",
            subject="project",
            source_layer="T23",
            source_name="resolution",
            status=ContinuityStatus.CURRENT,
            content_fingerprint="d" * 64,
            sequence=1,
        ),
    )


def test_same_inputs_same_recovery():
    context = {
        "project_fingerprint": "a" * 64,
        "state_fingerprint": "b" * 64,
        "branch": "reos-development",
        "commit_sha": "c" * 40,
    }

    first = recover_continuity(
        request=make_request(),
        evidence_items=make_evidence(),
        store=ContinuityStore(),
        project_context=context,
    )

    second = recover_continuity(
        request=make_request(),
        evidence_items=make_evidence(),
        store=ContinuityStore(),
        project_context=context,
    )

    assert (
        first.recovery_fingerprint
        == second.recovery_fingerprint
    )
