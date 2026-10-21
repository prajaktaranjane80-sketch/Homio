from .continuity_coordinator import recover_continuity
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)
from .continuity_store import ContinuityStore


def make_request(
    recovery_id: str,
    evidence_ids: tuple[str, ...],
) -> ContinuityRequest:
    return ContinuityRequest(
        recovery_id=recovery_id,
        project_id="HOMIO",
        source_resolution_id="resolution-1",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=evidence_ids,
        recovery_nonce=f"nonce-{recovery_id}",
    )


def make_evidence(
    evidence_id: str,
    *,
    subject: str,
    status: ContinuityStatus,
    fingerprint: str,
    sequence: int,
) -> ContinuityEvidence:
    return ContinuityEvidence(
        evidence_id=evidence_id,
        subject=subject,
        source_layer="T23",
        source_name="ContinuityFreshnessTest",
        status=status,
        content_fingerprint=fingerprint,
        sequence=sequence,
        canonical=True,
        immutable=True,
    )


def make_context() -> dict[str, str]:
    return {
        "project_fingerprint": "a" * 64,
        "state_fingerprint": "b" * 64,
        "branch": "reos-development",
        "commit_sha": "c" * 40,
    }


def test_stale_required_evidence_blocks_recovery():
    evidence = (
        make_evidence(
            "current",
            subject="project",
            status=ContinuityStatus.CURRENT,
            fingerprint="d" * 64,
            sequence=1,
        ),
        make_evidence(
            "stale",
            subject="state",
            status=ContinuityStatus.STALE,
            fingerprint="e" * 64,
            sequence=2,
        ),
    )

    result = recover_continuity(
        request=make_request(
            "stale-required-evidence",
            ("current", "stale"),
        ),
        evidence_items=evidence,
        store=ContinuityStore(),
        project_context=make_context(),
    )

    assert result.decision is ContinuityDecision.STALE
    assert result.snapshot is None
    assert result.stale_evidence_ids == ("stale",)


def test_unknown_required_evidence_blocks_even_with_current_evidence():
    evidence = (
        make_evidence(
            "current",
            subject="project",
            status=ContinuityStatus.CURRENT,
            fingerprint="d" * 64,
            sequence=1,
        ),
        make_evidence(
            "unknown",
            subject="state",
            status=ContinuityStatus.UNKNOWN,
            fingerprint="e" * 64,
            sequence=2,
        ),
    )

    result = recover_continuity(
        request=make_request(
            "unknown-required-evidence",
            ("current", "unknown"),
        ),
        evidence_items=evidence,
        store=ContinuityStore(),
        project_context=make_context(),
    )

    assert result.decision is ContinuityDecision.BLOCKED
    assert result.snapshot is None
    assert "UNKNOWN" in result.explanation
    assert "unknown" in result.explanation


def test_unknown_only_evidence_never_produces_a_recovered_snapshot():
    evidence = (
        make_evidence(
            "unknown",
            subject="project",
            status=ContinuityStatus.UNKNOWN,
            fingerprint="d" * 64,
            sequence=1,
        ),
    )

    result = recover_continuity(
        request=make_request(
            "unknown-only",
            ("unknown",),
        ),
        evidence_items=evidence,
        store=ContinuityStore(),
        project_context=make_context(),
    )

    assert result.decision is ContinuityDecision.BLOCKED
    assert result.snapshot is None
