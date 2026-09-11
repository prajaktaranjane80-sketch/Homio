from __future__ import annotations

import os
from pathlib import Path


class GitTransactionLockError(
    RuntimeError
):
    pass


class GitTransactionLock:
    def __init__(
        self,
        repository_root: Path | str,
    ) -> None:
        root = Path(
            repository_root
        ).resolve()

        self.path = (
            root
            / ".reos_t21_transaction.lock"
        )

        self._owned = False

    def acquire(self) -> None:
        if self.path.exists():
            raise GitTransactionLockError(
                "Another T21 transaction is active."
            )

        try:
            self.path.write_text(
                f"{os.getpid()}\n",
                encoding="utf-8",
                newline="\n",
            )
        except OSError as exc:
            raise GitTransactionLockError(
                "Unable to acquire T21 transaction lock."
            ) from exc

        self._owned = True

    def release(self) -> None:
        if not self._owned:
            return

        try:
            self.path.unlink(
                missing_ok=True
            )
        finally:
            self._owned = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        self.release()
