from .scheduler_identity import (
    fingerprint,
    scheduler_identity,
)


def test_fingerprint_is_deterministic():
    assert fingerprint(
        {"b": 2, "a": 1}
    ) == fingerprint(
        {"a": 1, "b": 2}
    )


def test_scheduler_identity_deterministic():
    first = scheduler_identity(
        scheduler_id="s1",
        loop_id="l1",
        loop_fingerprint="a",
        graph_fingerprint="b",
        policy_fingerprint="c",
        continuity_fingerprint="d",
        evidence_fingerprint="e",
    )

    second = scheduler_identity(
        scheduler_id="s1",
        loop_id="l1",
        loop_fingerprint="a",
        graph_fingerprint="b",
        policy_fingerprint="c",
        continuity_fingerprint="d",
        evidence_fingerprint="e",
    )

    assert first == second
