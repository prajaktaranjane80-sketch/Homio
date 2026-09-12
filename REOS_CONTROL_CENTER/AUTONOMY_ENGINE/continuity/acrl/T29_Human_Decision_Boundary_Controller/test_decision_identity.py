from .decision_identity import (
    decision_identity,
    fingerprint,
)


def test_fingerprint_deterministic():
    assert fingerprint({"b": 2, "a": 1}) == fingerprint(
        {"a": 1, "b": 2}
    )


def test_identity_changes_with_reconciliation():
    a = decision_identity(
        decision_id="D1",
        reconciliation_fingerprint="R1",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy_fingerprint="P1",
    )

    b = decision_identity(
        decision_id="D1",
        reconciliation_fingerprint="R2",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy_fingerprint="P1",
    )

    assert a != b
