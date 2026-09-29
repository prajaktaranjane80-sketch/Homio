from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from .trust_score import (
    TRUST_SCORE_MAX,
    TRUST_SCORE_MIN,
    TrustScore,
    TrustScoreConflictError,
    TrustScoreEngine,
    TrustScoreInsufficientEvidenceError,
    TrustScoreScopeError,
    TrustScoreValidationError,
    TrustScoringModel,
    TrustSignal,
)


AT = datetime(
    2026,
    9,
    29,
    6,
    0,
    tzinfo=timezone.utc,
)


def model() -> TrustScoringModel:
    return TrustScoringModel(
        model_version="1.0",
        category_weights_bps={
            "IDENTITY": 3000,
            "EVIDENCE": 4000,
            "HISTORY": 3000,
        },
    )


def signal(
    signal_id: str,
    *,
    tenant_id: str = "tenant-001",
    subject_id: str = "subject-001",
    category: str = "EVIDENCE",
    value: int = 80,
    evidence_reference: str = "evidence://001",
    source_reference: str = "source://001",
) -> TrustSignal:
    return TrustSignal(
        signal_id=signal_id,
        tenant_id=tenant_id,
        subject_id=subject_id,
        category=category,
        value=value,
        evidence_reference=evidence_reference,
        source_reference=source_reference,
        observed_at=AT,
    )


def test_model_is_versioned_and_immutable() -> None:
    item = model()

    assert item.model_version == "1.0"
    assert item.fingerprint
    assert item.category_weights_bps["EVIDENCE"] == 4000

    with pytest.raises(TypeError):
        item.category_weights_bps["EVIDENCE"] = 1  # type: ignore[index]


def test_empty_model_is_rejected() -> None:
    with pytest.raises(TrustScoreInsufficientEvidenceError):
        TrustScoringModel(
            model_version="1.0",
            category_weights_bps={},
        )


def test_invalid_model_weight_is_rejected() -> None:
    with pytest.raises(TrustScoreValidationError):
        TrustScoringModel(
            model_version="1.0",
            category_weights_bps={
                "EVIDENCE": 10001,
            },
        )


@pytest.mark.parametrize(
    "value",
    (-1, 101),
)
def test_signal_value_must_be_0_to_100(
    value: int,
) -> None:
    with pytest.raises(TrustScoreValidationError):
        signal("s1", value=value)


def test_signal_boolean_value_is_rejected() -> None:
    with pytest.raises(TrustScoreValidationError):
        signal("s1", value=True)  # type: ignore[arg-type]


def test_signal_requires_evidence_reference() -> None:
    with pytest.raises(TrustScoreValidationError):
        signal(
            "s1",
            evidence_reference="",
        )


def test_signal_requires_source_reference() -> None:
    with pytest.raises(TrustScoreValidationError):
        signal(
            "s1",
            source_reference=" ",
        )


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(TrustScoreValidationError):
        TrustSignal(
            signal_id="s1",
            tenant_id="t1",
            subject_id="s1",
            category="EVIDENCE",
            value=80,
            evidence_reference="e://1",
            source_reference="src://1",
            observed_at=datetime(
                2026, 9, 29, 6, 0
            ),
        )


def test_signal_metadata_is_immutable() -> None:
    item = TrustSignal(
        signal_id="s1",
        tenant_id="t1",
        subject_id="subject",
        category="EVIDENCE",
        value=90,
        evidence_reference="e://1",
        source_reference="src://1",
        observed_at=AT,
        metadata={"channel": "builder"},
    )

    with pytest.raises(TypeError):
        item.metadata["channel"] = "customer"  # type: ignore[index]


def test_signal_fingerprint_is_deterministic() -> None:
    first = signal("s1")
    second = signal("s1")

    assert first.fingerprint == second.fingerprint


def test_signal_compatibility_accepts_same_identity_and_payload() -> None:
    first = signal("s1")
    second = signal("s1")

    first.assert_compatible(second)


def test_signal_compatibility_rejects_conflicting_payload() -> None:
    first = signal("s1", value=80)
    second = signal("s1", value=81)

    with pytest.raises(TrustScoreConflictError):
        first.assert_compatible(second)


def test_signal_scope_is_tenant_and_subject_bound() -> None:
    item = signal("s1")

    item.assert_scope(
        tenant_id="tenant-001",
        subject_id="subject-001",
    )

    with pytest.raises(TrustScoreScopeError):
        item.assert_scope(
            tenant_id="tenant-999",
            subject_id="subject-001",
        )

    with pytest.raises(TrustScoreScopeError):
        item.assert_scope(
            tenant_id="tenant-001",
            subject_id="subject-999",
        )


def test_empty_signal_set_is_rejected() -> None:
    with pytest.raises(TrustScoreInsufficientEvidenceError):
        TrustScoreEngine.compute(
            tenant_id="tenant-001",
            subject_id="subject-001",
            signals=(),
            model=model(),
            computed_at=AT,
        )


def test_cross_tenant_signal_is_rejected() -> None:
    with pytest.raises(TrustScoreScopeError):
        TrustScoreEngine.compute(
            tenant_id="tenant-001",
            subject_id="subject-001",
            signals=(
                signal(
                    "s1",
                    tenant_id="tenant-999",
                ),
            ),
            model=model(),
            computed_at=AT,
        )


def test_cross_subject_signal_is_rejected() -> None:
    with pytest.raises(TrustScoreScopeError):
        TrustScoreEngine.compute(
            tenant_id="tenant-001",
            subject_id="subject-001",
            signals=(
                signal(
                    "s1",
                    subject_id="subject-999",
                ),
            ),
            model=model(),
            computed_at=AT,
        )


def test_unknown_category_is_not_silently_scored() -> None:
    with pytest.raises(TrustScoreInsufficientEvidenceError):
        TrustScoreEngine.compute(
            tenant_id="tenant-001",
            subject_id="subject-001",
            signals=(
                signal(
                    "s1",
                    category="UNKNOWN",
                ),
            ),
            model=model(),
            computed_at=AT,
        )


def test_duplicate_signal_identity_is_rejected() -> None:
    with pytest.raises(TrustScoreConflictError):
        TrustScoreEngine.compute(
            tenant_id="tenant-001",
            subject_id="subject-001",
            signals=(
                signal("s1"),
                signal("s1"),
            ),
            model=model(),
            computed_at=AT,
        )


def test_weighted_score_is_deterministic() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal(
                "s1",
                category="IDENTITY",
                value=100,
            ),
            signal(
                "s2",
                category="EVIDENCE",
                value=50,
            ),
        ),
        model=model(),
        computed_at=AT,
    )

    assert result.score == 71
    assert result.signal_ids == ("s1", "s2")
    assert result.total_weight_bps == 7000


def test_signal_order_does_not_change_score() -> None:
    first = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal(
                "s1",
                category="IDENTITY",
                value=100,
            ),
            signal(
                "s2",
                category="EVIDENCE",
                value=50,
            ),
        ),
        model=model(),
        computed_at=AT,
    )

    second = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal(
                "s2",
                category="EVIDENCE",
                value=50,
            ),
            signal(
                "s1",
                category="IDENTITY",
                value=100,
            ),
        ),
        model=model(),
        computed_at=AT,
    )

    assert first.score == second.score
    assert first.to_dict() == second.to_dict()


def test_score_is_within_bounds() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal(
                "s1",
                value=100,
            ),
        ),
        model=model(),
        computed_at=AT,
    )

    assert TRUST_SCORE_MIN <= result.score <= TRUST_SCORE_MAX


def test_all_zero_signal_produces_zero() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal(
                "s1",
                value=0,
            ),
        ),
        model=model(),
        computed_at=AT,
    )

    assert result.score == 0


def test_all_perfect_signal_produces_100() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal(
                "s1",
                value=100,
            ),
        ),
        model=model(),
        computed_at=AT,
    )

    assert result.score == 100


def test_score_preserves_model_fingerprint() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal("s1"),
        ),
        model=model(),
        computed_at=AT,
    )

    assert result.model_fingerprint == model().fingerprint
    assert result.model_version == "1.0"


def test_score_preserves_signal_fingerprints() -> None:
    source = signal("s1")

    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(source,),
        model=model(),
        computed_at=AT,
    )

    assert result.signal_fingerprints == (
        source.fingerprint,
    )


def test_contribution_records_model_weight() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal(
                "s1",
                category="EVIDENCE",
                value=75,
            ),
        ),
        model=model(),
        computed_at=AT,
    )

    assert len(result.contributions) == 1
    assert result.contributions[0].weight_bps == 4000
    assert result.contributions[0].weighted_value == 300000


def test_score_is_evidence_counted() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal("s1"),
            signal("s2"),
        ),
        model=model(),
        computed_at=AT,
    )

    assert result.evidence_count == 2


def test_score_scope_is_enforced() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(
            signal("s1"),
        ),
        model=model(),
        computed_at=AT,
    )

    result.assert_scope(
        tenant_id="tenant-001",
        subject_id="subject-001",
    )

    with pytest.raises(TrustScoreScopeError):
        result.assert_scope(
            tenant_id="tenant-999",
            subject_id="subject-001",
        )


def test_score_compatibility_accepts_same_identity_and_data() -> None:
    first = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(signal("s1"),),
        model=model(),
        computed_at=AT,
    )

    second = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(signal("s1"),),
        model=model(),
        computed_at=AT,
    )

    first.assert_compatible(second)


def test_model_change_changes_model_fingerprint() -> None:
    first = TrustScoringModel(
        model_version="1.0",
        category_weights_bps={
            "EVIDENCE": 4000,
        },
    )

    second = TrustScoringModel(
        model_version="1.1",
        category_weights_bps={
            "EVIDENCE": 4000,
        },
    )

    assert first.fingerprint != second.fingerprint


def test_score_serializes_to_json() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(signal("s1"),),
        model=model(),
        computed_at=AT,
    )

    payload = result.to_dict()

    json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )


def test_signal_serializes_to_json() -> None:
    payload = signal("s1").to_dict()

    json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )


def test_source_of_truth_is_trust_score() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(signal("s1"),),
        model=model(),
        computed_at=AT,
    )

    assert result.source_of_truth == "trust_score"


def test_trust_score_has_no_fraud_verdict_field() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(signal("s1"),),
        model=model(),
        computed_at=AT,
    )

    payload = result.to_dict()

    assert "fraud" not in payload
    assert "risk_decision" not in payload
    assert "authorization" not in payload
    assert "approval" not in payload


def test_metadata_is_preserved_without_becoming_score_authority() -> None:
    item = signal("s1")

    assert item.metadata == {}
    assert item.source_reference == "source://001"


def test_computed_at_is_normalized_to_utc() -> None:
    result = TrustScoreEngine.compute(
        tenant_id="tenant-001",
        subject_id="subject-001",
        signals=(signal("s1"),),
        model=model(),
        computed_at=AT,
    )

    assert result.computed_at.tzinfo is not None
    assert result.computed_at.utcoffset().total_seconds() == 0