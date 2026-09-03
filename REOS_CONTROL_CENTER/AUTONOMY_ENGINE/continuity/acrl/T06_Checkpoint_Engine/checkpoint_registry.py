"""ACRL T06 — checkpoint registry."""

from __future__ import annotations

from dataclasses import dataclass

from .checkpoint_engine import ExecutionCheckpoint
from .checkpoint_identity import (
    CheckpointIdentity,
    build_checkpoint_identity,
)


class CheckpointRegistryError(
    RuntimeError
):
    """Base registry error."""


class DuplicateCheckpointError(
    CheckpointRegistryError
):
    """Raised when the same checkpoint identity is registered twice."""


class CheckpointConflictError(
    CheckpointRegistryError
):
    """Raised when one checkpoint ID maps to different state."""


@dataclass(frozen=True)
class CheckpointRegistryEntry:
    """Immutable registry entry."""

    identity: CheckpointIdentity
    checkpoint: ExecutionCheckpoint


class CheckpointRegistry:
    """In-memory deterministic checkpoint registry."""

    def __init__(self) -> None:
        self._entries: dict[
            str,
            CheckpointRegistryEntry,
        ] = {}

    def register(
        self,
        checkpoint: ExecutionCheckpoint,
    ) -> CheckpointRegistryEntry:
        """Register one immutable checkpoint."""

        if not isinstance(
            checkpoint,
            ExecutionCheckpoint,
        ):
            raise TypeError(
                "checkpoint must be ExecutionCheckpoint."
            )

        identity = build_checkpoint_identity(
            checkpoint
        )

        identity_key = identity.identity_key()

        existing = self._entries.get(
            identity_key
        )

        if existing is not None:
            raise DuplicateCheckpointError(
                "Checkpoint identity already registered."
            )

        for entry in self._entries.values():
            if (
                entry.checkpoint.metadata.checkpoint_id
                == checkpoint.metadata.checkpoint_id
            ):
                if (
                    entry.identity.canonical_sha256
                    != identity.canonical_sha256
                ):
                    raise CheckpointConflictError(
                        "Checkpoint ID maps to conflicting checkpoint state."
                    )

        entry = CheckpointRegistryEntry(
            identity=identity,
            checkpoint=checkpoint,
        )

        self._entries[identity_key] = entry

        return entry

    def get(
        self,
        identity_key: str,
    ) -> CheckpointRegistryEntry | None:
        return self._entries.get(identity_key)

    def contains(
        self,
        identity_key: str,
    ) -> bool:
        return identity_key in self._entries

    def list_entries(
        self,
    ) -> tuple[CheckpointRegistryEntry, ...]:
        return tuple(
            self._entries[key]
            for key in sorted(self._entries)
        )

    def count(self) -> int:
        return len(self._entries)


__all__ = [
    "CheckpointConflictError",
    "CheckpointRegistry",
    "CheckpointRegistryEntry",
    "CheckpointRegistryError",
    "DuplicateCheckpointError",
]