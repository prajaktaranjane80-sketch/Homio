from .continuity_models import (
    ContinuityEvidence,
    ContinuityStatus,
)


def test_evidence_serialization():
    evidence = ContinuityEvidence(
        evidence_id="ev1",
        subject="project",
        source_layer="T03",
        source_name="StateSnapshot",
        status=ContinuityStatus.CURRENT,
        content_fingerprint="a" * 64,
        sequence=1,
        canonical=True,
    )

    data = evidence.to_dict()

    assert data["evidence_id"] == "ev1"
    assert data["canonical"] is True
