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


def test_conflicting_project_evidence_blocks_recovery():

    request = ContinuityRequest(
        recovery_id="ambiguous",
        project_id="HOMIO",
        source_resolution_id="resolution",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=("one", "two"),
        recovery_nonce="nonce",
    )

    evidence = (
        ContinuityEvidence(
            evidence_id="one",
            subject="project",
            source_layer="T03",
            source_name="ProjectDNA",
            status=ContinuityStatus.CURRENT,
            content_fingerprint="d" * 64,
            sequence=1,
            canonical=True,
        ),
        ContinuityEvidence(
            evidence_id="two",
            subject="project",
            source_layer="T03",
            source_name="ProjectDNA",
            status=ContinuityStatus.CURRENT,
            content_fingerprint="e" * 64,
            sequence=2,
            canonical=True,
        ),
    )

    result = recover_continuity(
        request=request,
        evidence_items=evidence,
        store=ContinuityStore(),
    )

    assert (
        result.decision
        is ContinuityDecision.AMBIGUOUS
    )

    assert result.snapshot is None
