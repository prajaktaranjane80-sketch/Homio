from reconciliation_identity import fingerprint, reconciliation_identity


def test_fingerprint_is_deterministic():
    assert fingerprint({"b": 2, "a": 1}) == fingerprint({"a": 1, "b": 2})


def test_identity_changes_with_scheduler():
    a = reconciliation_identity(
        reconciliation_id="R1",
        scheduler_fingerprint="S1",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy_fingerprint="P1",
    )
    b = reconciliation_identity(
        reconciliation_id="R1",
        scheduler_fingerprint="S2",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy_fingerprint="P1",
    )
    assert a != b
