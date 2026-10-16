
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from .git_lock import GitTransactionLock, GitTransactionLockError
from .git_read import GitReader


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
    request = make_request(["src/app.py"])

    assert validate_write_scope(
        request,
        GitPolicy(),
    ) == ("src/app.py",)


def test_protected_state_blocked():
    request = make_request(["data/state.json"])

    with pytest.raises(ValueError):
        validate_write_scope(
            request,
            GitPolicy(),
        )


def test_traversal_blocked():
    request = make_request(["../secret.txt"])

    with pytest.raises(ValueError):
        validate_write_scope(
            request,
            GitPolicy(),
        )


def test_safe_path():
    assert is_safe_repository_path("src/app.py")


def test_absolute_path_rejected():
    assert not is_safe_repository_path("/etc/passwd")


def test_parent_path_rejected():
    assert not is_safe_repository_path("../secret.py")


@pytest.mark.parametrize(
    "path",
    [
        "C:/secret.py",
        r"C:\secret.py",
        "//server/share/file.py",
        "src//app.py",
        "src/./app.py",
        "src/../secret.py",
        "src/app.py/",
        " src/app.py",
        "src/app.py ",
        "src/\x00app.py",
        "src/\napp.py",
        "",
    ],
)
def test_unsafe_repository_paths_are_rejected(path: str):
    assert not is_safe_repository_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "src/app.py",
        "REOS_CONTROL_CENTER/Frontend/src/app/page.tsx",
        "src/file name.py",
    ],
)
def test_valid_repository_paths_are_accepted(path: str):
    assert is_safe_repository_path(path)


def test_force_push_policy_rejected():
    with pytest.raises(ValueError):
        validate_policy(
            GitPolicy(allow_force_push=True),
        )


def test_protected_state_path_is_detected():
    assert is_protected_path(
        "REOS_CONTROL_CENTER/data/state.json",
        GitPolicy(),
    )
