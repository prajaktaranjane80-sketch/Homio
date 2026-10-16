from __future__ import annotations

import os
from pathlib import Path


class GitTransactionLockError(RuntimeError):
    pass


class GitTransactionLock:
    """Atomic repository lock with file-identity-aware release."""

    def __init__(
        self,
        repository_root: Path | str,
    ) -> None:
        root = Path(repository_root).resolve()

        self.path = root / ".reos_t21_transaction.lock"
        self._owned = False
        self._identity: tuple[int, int] | None = None

    def _current_identity(self) -> tuple[int, int] | None:
        try:
            stat_result = os.stat(
                self.path,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise GitTransactionLockError(
                "Unable to inspect T21 transaction lock."
            ) from exc

        return (
            stat_result.st_dev,
            stat_result.st_ino,
        )

    def _path_is_owned(self) -> bool:
        if self._identity is None:
            return False

        return self._current_identity() == self._identity

    def acquire(self) -> None:
        if self._owned:
            raise GitTransactionLockError(
                "This T21 lock instance already owns a lock."
            )

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

        stat_result = os.fstat(descriptor)
        self._identity = (
            stat_result.st_dev,
            stat_result.st_ino,
        )

        try:
            with os.fdopen(
                descriptor,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as lock_file:
                lock_file.write(
                    f"{os.getpid()}\n"
                )
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except Exception as exc:
            # Remove only the exact file this instance created.
            try:
                if self._path_is_owned():
                    self.path.unlink(missing_ok=True)
            except OSError:
                pass

            self._identity = None

            raise GitTransactionLockError(
                "Unable to initialize T21 transaction lock."
            ) from exc

        self._owned = True

    def release(self) -> None:
        if not self._owned:
            return

        current_identity = self._current_identity()

        if current_identity is None:
            self._owned = False
            self._identity = None
            return

        if current_identity != self._identity:
            # The path was replaced. Never delete the replacement.
            self._owned = False
            self._identity = None
            raise GitTransactionLockError(
                "T21 lock ownership changed; replacement was not removed."
            )

        try:
            self.path.unlink()
        except OSError as exc:
            raise GitTransactionLockError(
                "Unable to release T21 transaction lock."
            ) from exc

        self._owned = False
        self._identity = None

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
