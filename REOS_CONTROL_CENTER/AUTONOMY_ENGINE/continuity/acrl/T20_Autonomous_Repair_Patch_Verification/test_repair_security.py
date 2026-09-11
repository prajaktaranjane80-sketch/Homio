from __future__ import annotations

import pytest

from .repair_models import RepairPolicy, RepairRequest
from .repair_scope import validate_scope


def make_request(
    patch: str,
    allowed: tuple[str, ...],
):
    return RepairRequest(
        repair_id="security-001",
        authorization_fingerprint="a" * 64,
        authorization_nonce="nonce-security",
        diagnosis_fingerprint="b" * 64,
        impact_fingerprint="c" * 64,
        baseline_fingerprint="d" * 64,
        allowed_paths=allowed,
        forbidden_paths=(),
        candidate_patch=patch,
    )


def test_path_traversal_is_blocked():
    patch = (
        "--- a/../secret.py\n"
        "+++ b/../secret.py\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )

    request = make_request(
        patch,
        ("../secret.py",),
    )

    with pytest.raises(ValueError):
        validate_scope(
            request,
            RepairPolicy(),
        )


def test_unrelated_file_is_blocked():
    patch = (
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )

    request = make_request(
        patch,
        ("src/other.py",),
    )

    with pytest.raises(ValueError):
        validate_scope(
            request,
            RepairPolicy(),
        )


def test_protected_state_is_blocked():
    patch = (
        "--- a/data/state.json\n"
        "+++ b/data/state.json\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )

    request = make_request(
        patch,
        ("data/state.json",),
    )

    with pytest.raises(ValueError):
        validate_scope(
            request,
            RepairPolicy(),
        )
