import pytest

from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
)
from .evidence_policy import (
    EvidencePolicy,
)
from .evidence_validation import (
    validate_evidence,
)


def test_mutable_evidence_is_blocked():
    evidence = EvidenceReference(
        evidence_id="mutable",
        subject="state",
        evidence_type=EvidenceType.STATE,
        authority=EvidenceAuthority.CANONICAL_STATE,
        status=EvidenceStatus.CURRENT,
        source_layer="T03",
        source_name="State",
        content_fingerprint="a" * 64,
        sequence=1,
        immutable=False,
    )

    with pytest.raises(ValueError):
        validate_evidence(
            evidence,
            EvidencePolicy(),
        )


def test_invalid_evidence_is_blocked():
    evidence = EvidenceReference(
        evidence_id="invalid",
        subject="state",
        evidence_type=EvidenceType.STATE,
        authority=EvidenceAuthority.CANONICAL_STATE,
        status=EvidenceStatus.INVALID,
        source_layer="T03",
        source_name="State",
        content_fingerprint="a" * 64,
        sequence=1,
    )

    with pytest.raises(ValueError):
        validate_evidence(
            evidence,
            EvidencePolicy(),
        )
