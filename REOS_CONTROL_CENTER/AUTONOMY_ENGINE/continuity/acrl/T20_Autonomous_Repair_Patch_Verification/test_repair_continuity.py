from __future__ import annotations

from .repair_continuity import (
    RepairContinuityDecision,
    RepairContinuityValidationError,
    build_repair_continuity_signal,
)
from .repair_models import (
    RepairDecision,
    RepairReason,
    RepairResult,
)


def make_result(
    decision: RepairDecision,
) -> RepairResult:
    return RepairResult(
        schema_version="1.0",
        decision=decision,
        reason=(
            RepairReason.VALID
            if decision is RepairDecision.VERIFIED
            else RepairReason.VERIFICATION_REQUIRED
        ),
        repair_id="repair-continuity-001",
        authorization_fingerprint="a" * 64,
        diagnosis_fingerprint="b" * 64,
        baseline_fingerprint="c" * 64,
        patch_fingerprint="d" * 64,
        final_tree_fingerprint="e" * 64,
        changed_paths=("src/app.py",),
        attempt=1,
        verification=None,
        evidence_fingerprint="f" * 64,
    )


def test_verified_repair_requires_context_refresh() -> None:
    signal = build_repair_continuity_signal(
        result=make_result(
            RepairDecision.VERIFIED
        ),
        previous_context_fingerprint="1" * 64,
    )

    assert (
        signal.decision
        is RepairContinuityDecision.REFRESH_REQUIRED
    )

    assert signal.requires_context_refresh is True
    assert signal.verify_integrity() is True


def test_unverified_repair_invalidates_context() -> None:
    signal = build_repair_continuity_signal(
        result=make_result(
            RepairDecision.REPAIR_APPLIED
        ),
        previous_context_fingerprint="1" * 64,
    )

    assert (
        signal.decision
        is RepairContinuityDecision.INVALIDATE_REQUIRED
    )

    assert signal.requires_context_refresh is True
    assert signal.verify_integrity() is True


def test_blocked_repair_invalidates_context() -> None:
    signal = build_repair_continuity_signal(
        result=make_result(
            RepairDecision.BLOCKED
        ),
        previous_context_fingerprint="1" * 64,
    )

    assert (
        signal.decision
        is RepairContinuityDecision.INVALIDATE_REQUIRED
    )

    assert signal.requires_context_refresh is True


def test_invalid_context_fingerprint_is_rejected() -> None:
    try:
        build_repair_continuity_signal(
            result=make_result(
                RepairDecision.VERIFIED
            ),
            previous_context_fingerprint="invalid",
        )
    except RepairContinuityValidationError:
        return

    raise AssertionError(
        "Invalid context fingerprint was accepted."
    )


def test_signal_is_deterministic() -> None:
    first = build_repair_continuity_signal(
        result=make_result(
            RepairDecision.VERIFIED
        ),
        previous_context_fingerprint="1" * 64,
    )

    second = build_repair_continuity_signal(
        result=make_result(
            RepairDecision.VERIFIED
        ),
        previous_context_fingerprint="1" * 64,
    )

    assert first == second
