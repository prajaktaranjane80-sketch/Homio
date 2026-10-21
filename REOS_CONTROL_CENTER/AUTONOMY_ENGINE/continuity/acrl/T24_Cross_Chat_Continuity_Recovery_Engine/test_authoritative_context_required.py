from .continuity_coordinator import recover_continuity
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)
from .continuity_store import ContinuityStore


def make_request(
    recovery_id: str = "context-required",
) -> ContinuityRequest:
    return ContinuityRequest(
        recovery_id=recovery_id,
        project_id="HOMIO",
        source_resolution_id="resolution-1",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=("project",),
        recovery_nonce="nonce-1",
    )


def make_evidence() -> tuple[ContinuityEvidence, ...]:
    return (
        ContinuityEvidence(
            evidence_id="project",
            subject="project",
            source_layer="T23",
            source_name="ProjectResolution",
            status=ContinuityStatus.CURRENT,
            content_fingerprint="d" * 64,
            sequence=1,
            canonical=True,
            immutable=True,
        ),
    )


def make_context() -> dict[str, str]:
    return {
        "project_fingerprint": "a" * 64,
        "state_fingerprint": "b" * 64,
        "branch": "reos-development",
        "commit_sha": "c" * 40,
    }


def test_missing_context_does_not_fall_back_to_expected_values():
    store = ContinuityStore()

    result = recover_continuity(
        request=make_request(),
        evidence_items=make_evidence(),
        store=store,
        project_context=None,
    )

    assert result.decision is ContinuityDecision.BLOCKED
    assert result.reason == "AUTHORITATIVE_CONTEXT_REQUIRED"
    assert result.snapshot is None
    assert store.get("context-required") is None


def test_partial_context_does_not_use_missing_request_values():
    store = ContinuityStore()

    result = recover_continuity(
        request=make_request("partial-context"),
        evidence_items=make_evidence(),
        store=store,
        project_context={
            "branch": "reos-development",
            "commit_sha": "c" * 40,
        },
    )

    assert result.decision is ContinuityDecision.BLOCKED
    assert result.reason == "AUTHORITATIVE_CONTEXT_REQUIRED"
    assert result.snapshot is None
    assert "project_fingerprint" in result.explanation
    assert "state_fingerprint" in result.explanation
    assert store.get("partial-context") is None


def test_unknown_context_values_are_not_authoritative():
    context = make_context()
    context["branch"] = "UNKNOWN"

    result = recover_continuity(
        request=make_request("unknown-context"),
        evidence_items=make_evidence(),
        store=ContinuityStore(),
        project_context=context,
    )

    assert result.decision is ContinuityDecision.BLOCKED
    assert result.reason == "AUTHORITATIVE_CONTEXT_REQUIRED"
    assert result.snapshot is None


def test_mismatched_observed_context_fails_integrity_check():
    context = make_context()
    context["project_fingerprint"] = "f" * 64

    result = recover_continuity(
        request=make_request("mismatched-context"),
        evidence_items=make_evidence(),
        store=ContinuityStore(),
        project_context=context,
    )

    assert result.decision is ContinuityDecision.INTEGRITY_FAILURE
    assert result.reason == "PROJECT_FINGERPRINT_MISMATCH"
    assert result.snapshot is None
