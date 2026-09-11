from __future__ import annotations

import pytest

from .git_models import (
    GitOperation,
    GitPolicy,
    GitTransactionRequest,
)
from .git_scope import (
    validate_write_scope,
)


def make_request(paths):
    return GitTransactionRequest(
        operation=GitOperation.COMMIT,
        repository_root=".",
        expected_branch="main",
        expected_head_sha="a" * 40,
        transaction_id="tx-001",
        repair_id="repair-001",
        repair_fingerprint="b" * 64,
        changed_paths=tuple(paths),
        authorization_fingerprint="c" * 64,
        authorization_nonce="nonce",
    )


def test_valid_scope():
    request = make_request(
        ["src/app.py"]
    )

    assert validate_write_scope(
        request,
        GitPolicy(),
    ) == ("src/app.py",)


def test_protected_state_blocked():
    request = make_request(
        ["data/state.json"]
    )

    with pytest.raises(ValueError):
        validate_write_scope(
            request,
            GitPolicy(),
        )


def test_traversal_blocked():
    request = make_request(
        ["../secret.txt"]
    )

    with pytest.raises(ValueError):
        validate_write_scope(
            request,
            GitPolicy(),
        )
