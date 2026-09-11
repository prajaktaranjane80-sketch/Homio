from __future__ import annotations

import pytest

from .repair_models import RepairPolicy, RepairRequest
from .repair_scope import (
    patch_paths,
    validate_scope,
)


def make_request(
    patch: str,
    allowed: tuple[str, ...],
):
    return RepairRequest(
        repair_id="repair-001",
        authorization_fingerprint="a" * 64,
        authorization_nonce="nonce-001",
        diagnosis_fingerprint="b" * 64,
        impact_fingerprint="c" * 64,
        baseline_fingerprint="d" * 64,
        allowed_paths=allowed,
        forbidden_paths=(),
        candidate_patch=patch,
    )


def test_patch_paths_are_deterministic():
    patch = (
        "--- a/src/b.py\n"
        "+++ b/src/b.py\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )

    assert patch_paths(patch) == (
        "src/b.py",
    )


def test_scope_accepts_authorized_path():
    patch = (
        "--- a/src/b.py\n"
        "+++ b/src/b.py\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )

    request = make_request(
        patch,
        ("src/b.py",),
    )

    assert validate_scope(
        request,
        RepairPolicy(),
    ) == ("src/b.py",)


def test_scope_blocks_escape():
    patch = (
        "--- a/src/b.py\n"
        "+++ b/src/other.py\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )

    request = make_request(
        patch,
        ("src/b.py",),
    )

    with pytest.raises(ValueError):
        validate_scope(
            request,
            RepairPolicy(),
        )


def test_scope_blocks_state_file():
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
