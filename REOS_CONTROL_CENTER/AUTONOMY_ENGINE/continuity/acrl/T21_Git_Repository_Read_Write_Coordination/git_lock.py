from __future__ import annotations

import os
from pathlib import Path


class GitTransactionLockError(RuntimeError):
    pass


class GitTransactionLock:
    """Atomic, exclusive lock for one T21 repository transaction."""

    def __init__(
        self,
        repository_root: Path | str,
    ) -> None:
        root = Path(repository_root).resolve()

        self.path = root / ".reos_t21_transaction.lock"
        self._owned = False

    def acquire(self) -> None:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY

        try:
            descriptor = os.open(
                self.path,
                flags,
                0o600,
            )
        except FileExistsError as exc:
            raise GitTransactionLockError(
                "Another T21 transaction is active."
            ) from exc
        except OSError as exc:
            raise GitTransactionLockError(
                "Unable to acquire T21 transaction lock."
            ) from exc

        try:
            with os.fdopen(
                descriptor,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as lock_file:
                lock_file.write(f"{os.getpid()}\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError as exc:
            try:
                self.path.unlink(missing_ok=True)
            except OSError:
                pass

            raise GitTransactionLockError(
                "Unable to initialize T21 transaction lock."
            ) from exc

        self._owned = True

    def release(self) -> None:
        if not self._owned:
            return

        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            raise GitTransactionLockError(
                "Unable to release T21 transaction lock."
            ) from exc
        else:
            self._owned = False

    def __enter__(self) -> GitTransactionLock:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.release()
