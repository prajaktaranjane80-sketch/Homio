from __future__ import annotations

import subprocess

from .git_read import GitReader


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


def commit(path):
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


def test_reader_reads_repository(tmp_path):
    init_repo(tmp_path)

    (tmp_path / "file.txt").write_text(
        "hello\n",
        encoding="utf-8",
    )

    commit(tmp_path)

    snapshot = GitReader(
        tmp_path
    ).snapshot()

    assert snapshot.branch
    assert len(snapshot.head_sha) == 40
    assert snapshot.working_tree_clean
