from __future__ import annotations

import pytest

from .git_lock import (
    GitTransactionLock,
    GitTransactionLockError,
)


def test_concurrent_lock_is_blocked(tmp_path):
    first = GitTransactionLock(
        tmp_path
    )

    second = GitTransactionLock(
        tmp_path
    )

    first.acquire()

    try:
        with pytest.raises(
            GitTransactionLockError
        ):
            second.acquire()
    finally:
        first.release()
