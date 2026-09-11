from __future__ import annotations

import subprocess

from .git_repository import GitRepository
from .git_stage import (
    stage_exact_paths,
    staged_paths,
)
from .git_models import GitPolicy


def init_repo(path):
    subprocess.run(
        ["git", "init"],
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


def test_exact_staging(tmp_path):
    init_repo(tmp_path)

    (tmp_path / "a.txt").write_text(
        "a\n",
        encoding="utf-8",
    )

    (tmp_path / "b.txt").write_text(
        "b\n",
        encoding="utf-8",
    )

    repository = GitRepository(
        tmp_path
    )

    stage_exact_paths(
        repository,
        ("a.txt",),
        GitPolicy(),
    )

    assert staged_paths(
        repository
    ) == ("a.txt",)
