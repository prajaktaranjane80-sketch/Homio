import pytest

from .continuity_models import (
    ContinuityEvidence,
    ContinuityStatus,
)
from .continuity_policy import (
    ContinuityPolicy,
)
from .continuity_validation import (
    validate_evidence,
)


def test_mutable_evidence_blocked():
    evidence = ContinuityEvidence(
        evidence_id="mutable",
        subject="state",
        source_layer="T03",
        source_name="state",
        status=ContinuityStatus.CURRENT,
        content_fingerprint="a" * 64,
        sequence=1,
        immutable=False,
    )

    with pytest.raises(ValueError):
        validate_evidence(
            evidence,
            ContinuityPolicy(),
        )


def test_invalid_evidence_blocked():
    evidence = ContinuityEvidence(
        evidence_id="invalid",
        subject="state",
        source_layer="T03",
        source_name="state",
        status=ContinuityStatus.INVALID,
        content_fingerprint="a" * 64,
        sequence=1,
    )

    with pytest.raises(ValueError):
        validate_evidence(
            evidence,
            ContinuityPolicy(),
        )
