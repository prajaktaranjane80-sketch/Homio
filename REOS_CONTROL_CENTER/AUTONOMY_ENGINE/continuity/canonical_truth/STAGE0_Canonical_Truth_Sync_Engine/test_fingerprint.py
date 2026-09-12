from .truth_fingerprint import digest


def test_digest_is_deterministic():
    assert digest({"b": 2, "a": 1}) == digest({"a": 1, "b": 2})
