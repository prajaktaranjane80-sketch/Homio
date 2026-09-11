import pytest

from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
    ResolutionRequest,
)
from .evidence_policy import (
    EvidencePolicy,
)
from .evidence_validation import (
    validate_evidence,
    validate_resolution_request,
)


def make_evidence():
    return EvidenceReference(
        evidence_id="ev-1",
        subject="repository:HEAD",
        evidence_type=EvidenceType.GIT,
        authority=EvidenceAuthority.GIT_TRANSACTION,
        status=EvidenceStatus.CURRENT,
        source_layer="T21",
        source_name="GitTransactionResult",
        content_fingerprint="a" * 64,
        sequence=1,
    )


def test_valid_evidence():
    validate_evidence(
        make_evidence(),
        EvidencePolicy(),
    )


def test_invalid_fingerprint():
    evidence = EvidenceReference(
        evidence_id="ev",
        subject="x",
        evidence_type=EvidenceType.GIT,
        authority=EvidenceAuthority.GIT_TRANSACTION,
        status=EvidenceStatus.CURRENT,
        source_layer="T21",
        source_name="x",
        content_fingerprint="bad",
        sequence=1,
    )

    with pytest.raises(ValueError):
        validate_evidence(
            evidence,
            EvidencePolicy(),
        )


def test_duplicate_request_ids_blocked():
    request = ResolutionRequest(
        resolution_id="r1",
        subject="x",
        evidence_ids=(
            "ev1",
            "ev1",
        ),
    )

    with pytest.raises(ValueError):
        validate_resolution_request(
            request
        )
