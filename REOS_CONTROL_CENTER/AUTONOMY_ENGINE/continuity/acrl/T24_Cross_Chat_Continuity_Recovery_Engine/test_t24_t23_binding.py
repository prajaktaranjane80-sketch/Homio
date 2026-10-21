from dataclasses import replace

from ._t23_test_support import build_t23_source_store
from .continuity_coordinator import recover_continuity
from .continuity_models import ContinuityDecision
from .continuity_store import ContinuityStore
from .test_continuity_coordinator import (
    make_context,
    make_evidence,
    make_request,
)


def test_claimed_provenance_without_t23_store_blocks_recovery():
    request = make_request()
    evidence = make_evidence()
    continuity_store = ContinuityStore()

    result = recover_continuity(
        request=request,
        evidence_items=evidence,
        store=continuity_store,
        project_context=make_context(),
        source_resolution_store=None,
    )

    assert result.decision is ContinuityDecision.BLOCKED
    assert result.reason == "T23_RESOLUTION_REQUIRED"
    assert result.snapshot is None
    assert continuity_store.get(request.recovery_id) is None


def test_mismatched_t23_evidence_fingerprint_blocks_recovery():
    request = make_request()
    evidence = make_evidence()

    mismatched_source_evidence = tuple(
        replace(
            item,
            content_fingerprint="f" * 64,
        )
        if item.evidence_id == "state"
        else item
        for item in evidence
    )

    source_resolution_store = build_t23_source_store(
        request,
        mismatched_source_evidence,
    )
    continuity_store = ContinuityStore()

    result = recover_continuity(
        request=request,
        evidence_items=evidence,
        store=continuity_store,
        project_context=make_context(),
        source_resolution_store=source_resolution_store,
    )

    assert result.decision is ContinuityDecision.BLOCKED
    assert result.reason == "T23_EVIDENCE_BINDING_MISMATCH"
    assert result.snapshot is None
    assert continuity_store.get(request.recovery_id) is None
