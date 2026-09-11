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
):
    return ContinuityEvidence(
        evidence_id=evidence_id,
        subject=subject,
        source_layer="T23",
        source_name="test",
        status=status,
        content_fingerprint=content,
        sequence=1,
    )


def test_current_evidence_selected():
    selected, missing, stale = (
        select_current_evidence(
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
    )

    assert len(selected) == 1
    assert not missing
    assert not stale


def test_missing_detected():
    _, missing, _ = (
        select_current_evidence(
            (),
            ("ev",),
        )
    )

    assert missing == ("ev",)


def test_conflict_detected():
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

    assert set(conflicts) == {
        "a",
        "b",
    }
