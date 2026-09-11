from __future__ import annotations

import subprocess

from .git_commit import (
    create_commit,
    verify_commit,
)
from .git_models import GitPolicy
from .git_repository import GitRepository
from .git_stage import stage_exact_paths


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


def test_create_and_verify_commit(tmp_path):
    init_repo(tmp_path)
    initial_commit(tmp_path)

    (tmp_path / "file.txt").write_text(
        "two\n",
        encoding="utf-8",
    )

    repository = GitRepository(
        tmp_path
    )

    stage_exact_paths(
        repository,
        ("file.txt",),
        GitPolicy(),
    )

    sha = create_commit(
        repository,
        "test: update file",
        GitPolicy(),
    )

    assert len(sha) == 40
    assert verify_commit(
        repository,
        sha,
    )
