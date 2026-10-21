import pytest

from .continuity_evidence import (
    detect_identity_conflicts,
    select_current_evidence,
)
from .continuity_models import (
    ContinuityEvidence,
    ContinuityStatus,
)


def make(
    evidence_id,
    subject,
    status,
    content,
    *,
    canonical=False,
    immutable=True,
):
    return ContinuityEvidence(
        evidence_id=evidence_id,
        subject=subject,
        source_layer="T23",
        source_name="test",
        status=status,
        content_fingerprint=content,
        sequence=1,
        canonical=canonical,
        immutable=immutable,
    )


def test_current_evidence_selected():
    selected, missing, stale = select_current_evidence(
        (
            make(
                "ev",
                "state",
                ContinuityStatus.CURRENT,
                "a" * 64,
            ),
        ),
        ("ev",),
    )

    assert len(selected) == 1
    assert not missing
    assert not stale


def test_missing_detected():
    _, missing, _ = select_current_evidence((), ("ev",))
    assert missing == ("ev",)


def test_equally_ranked_conflicting_evidence_is_detected():
    conflicts = detect_identity_conflicts(
        (
            make(
                "a",
                "state",
                ContinuityStatus.CURRENT,
                "a" * 64,
            ),
            make(
                "b",
                "state",
                ContinuityStatus.CURRENT,
                "b" * 64,
            ),
        )
    )

    assert set(conflicts) == {"a", "b"}


def test_current_canonical_evidence_outranks_noncanonical_evidence():
    canonical = make(
        "canonical",
        "state",
        ContinuityStatus.CURRENT,
        "a" * 64,
        canonical=True,
    )
    noncanonical = make(
        "noncanonical",
        "state",
        ContinuityStatus.CURRENT,
        "b" * 64,
        canonical=False,
    )

    assert detect_identity_conflicts(
        (canonical, noncanonical)
    ) == ()

    selected, missing, stale = select_current_evidence(
        (canonical, noncanonical),
        ("noncanonical", "canonical"),
    )

    assert tuple(item.evidence_id for item in selected) == (
        "canonical",
    )
    assert not missing
    assert not stale


def test_equally_ranked_canonical_conflict_fails_closed():
    conflicts = detect_identity_conflicts(
        (
            make(
                "a",
                "state",
                ContinuityStatus.CURRENT,
                "a" * 64,
                canonical=True,
            ),
            make(
                "b",
                "state",
                ContinuityStatus.CURRENT,
                "b" * 64,
                canonical=True,
            ),
        )
    )

    assert set(conflicts) == {"a", "b"}


def test_duplicate_ids_are_explicitly_reported():
    conflicts = detect_identity_conflicts(
        (
            make(
                "duplicate",
                "state",
                ContinuityStatus.CURRENT,
                "a" * 64,
            ),
            make(
                "duplicate",
                "state",
                ContinuityStatus.CURRENT,
                "a" * 64,
            ),
        )
    )

    assert conflicts == ("duplicate",)

    with pytest.raises(ValueError, match="Duplicate continuity evidence IDs"):
        select_current_evidence(
            (
                make(
                    "duplicate",
                    "state",
                    ContinuityStatus.CURRENT,
                    "a" * 64,
                ),
                make(
                    "duplicate",
                    "state",
                    ContinuityStatus.CURRENT,
                    "a" * 64,
                ),
            ),
            ("duplicate",),
        )


def test_current_evidence_ranks_above_stale_for_conflict_analysis():
    current = make(
        "current",
        "state",
        ContinuityStatus.CURRENT,
        "a" * 64,
        canonical=True,
    )
    stale = make(
        "stale",
        "state",
        ContinuityStatus.STALE,
        "b" * 64,
        canonical=True,
    )

    assert detect_identity_conflicts((current, stale)) == ()
