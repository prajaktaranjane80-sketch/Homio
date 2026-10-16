
from __future__ import annotations

from pathlib import Path

import pytest

from .git_lock import GitTransactionLock, GitTransactionLockError
from .git_read import GitReader


def init_repo(path: Path) -> None:
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


def test_second_lock_is_rejected_while_first_is_held(
    tmp_path: Path,
):
    first = GitTransactionLock(tmp_path)
    second = GitTransactionLock(tmp_path)

    first.acquire()

    try:
        with pytest.raises(GitTransactionLockError):
            second.acquire()
    finally:
        first.release()

    assert not first.path.exists()


def test_release_does_not_delete_replacement_lock_file(
    tmp_path: Path,
):
    lock = GitTransactionLock(tmp_path)
    lock.acquire()

    displaced_original = tmp_path / ".original-t21-lock"
    lock.path.replace(displaced_original)

    lock.path.write_text(
        "replacement lock\n",
        encoding="utf-8",
    )

    try:
        with pytest.raises(GitTransactionLockError):
            lock.release()

        assert lock.path.is_file()
        assert lock.path.read_text(encoding="utf-8") == "replacement lock\n"
        assert displaced_original.is_file()
    finally:
        lock.path.unlink(missing_ok=True)
        displaced_original.unlink(missing_ok=True)


def test_lock_does_not_make_repository_dirty(
    tmp_path: Path,
):
    init_repo(tmp_path)
    reader = GitReader(tmp_path)
    assert reader.snapshot().working_tree_clean

    lock = GitTransactionLock(tmp_path)
    lock.acquire()

    try:
        assert reader.snapshot().working_tree_clean
    finally:
        lock.release()

    assert reader.snapshot().working_tree_clean


def test_lock_context_cleanup_removes_owned_lock_file(
    tmp_path: Path,
):
    lock = GitTransactionLock(tmp_path)

    with lock:
        assert lock.path.is_file()

    assert not lock.path.exists()
