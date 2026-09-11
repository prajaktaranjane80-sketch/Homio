from __future__ import annotations

import subprocess

from .git_models import (
    GitOperation,
    GitTransactionRequest,
)
from .git_read import GitReader
from .git_transaction import (
    execute_git_transaction,
)


def init_repo(path):
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "T21 Test"],
        cwd=path,
        check=True,
    )


def initial_commit(path):
    (path / "file.txt").write_text(
        "one\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "file.txt"],
        cwd=path,
        check=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def make_request(path):
    snapshot = GitReader(
        path
    ).snapshot()

    return GitTransactionRequest(
        operation=GitOperation.COMMIT,
        repository_root=str(path),
        expected_branch=snapshot.branch,
        expected_head_sha=snapshot.head_sha,
        transaction_id="tx-001",
        repair_id="repair-001",
        repair_fingerprint="a" * 64,
        changed_paths=("file.txt",),
        commit_message="test: verified repair",
        authorization_fingerprint="b" * 64,
        authorization_nonce="nonce-001",
    ), snapshot


def test_dirty_tree_is_blocked(tmp_path):
    init_repo(tmp_path)
    initial_commit(tmp_path)

    (tmp_path / "file.txt").write_text(
        "two\n",
        encoding="utf-8",
    )

    request, _ = make_request(
        tmp_path
    )

    result = execute_git_transaction(
        request=request,
        authorization=None,
    )

    assert result.decision.value == "BLOCKED"
    assert result.reason.value == (
        "DIRTY_WORKTREE"
    )
