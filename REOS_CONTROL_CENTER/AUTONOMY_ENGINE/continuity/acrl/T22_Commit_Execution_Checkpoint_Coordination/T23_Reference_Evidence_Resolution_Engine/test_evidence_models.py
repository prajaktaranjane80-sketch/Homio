from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
)


def test_evidence_serialization():
    evidence = EvidenceReference(
        evidence_id="ev-1",
        subject="repository:HEAD",
        evidence_type=EvidenceType.GIT,
        authority=EvidenceAuthority.GIT_TRANSACTION,
        status=EvidenceStatus.CURRENT,
        source_layer="T21",
        source_name="GitTransactionResult",
        content_fingerprint="a" * 64,
        sequence=1,
        canonical=False,
    )

    payload = evidence.to_dict()

    assert (
        payload["evidence_id"]
        == "ev-1"
    )

    assert (
        payload["authority"]
        == "GIT_TRANSACTION"
    )
