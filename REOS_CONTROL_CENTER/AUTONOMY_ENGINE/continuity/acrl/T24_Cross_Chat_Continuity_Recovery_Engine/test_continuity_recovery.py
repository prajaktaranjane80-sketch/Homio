from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)
from .continuity_policy import (
    ContinuityPolicy,
)
from .continuity_recovery import (
    evaluate_recovery,
)


def make_request():
    return ContinuityRequest(
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


def test_recovery_is_possible():
    decision, conflicts, missing, stale, _ = (
        evaluate_recovery(
            request=make_request(),
            evidence_items=make_evidence(),
            policy=ContinuityPolicy(),
        )
    )

    assert (
        decision
        is ContinuityDecision.RECOVERED
    )

    assert not conflicts
    assert not missing
    assert not stale
