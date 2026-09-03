"""ACRL T06 — checkpoint provenance."""

from __future__ import annotations

from dataclasses import dataclass

from .checkpoint_engine import (
    CheckpointEngine,
    ExecutionCheckpoint,
)
from .checkpoint_identity import (
    build_checkpoint_identity,
)


@dataclass(frozen=True)
class CheckpointProvenance:
    """Immutable provenance attached to a checkpoint."""

    authoritative_source: str
    authoritative_state_path: str
    checkpoint_id: str
    created_at: str
    schema_version: str
    state_fingerprint: str
    checkpoint_identity: str

    def to_dict(self) -> dict[str, str]:
        return {
            "authoritative_source": (
                self.authoritative_source
            ),
            "authoritative_state_path": (
                self.authoritative_state_path
            ),
            "checkpoint_id": self.checkpoint_id,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
            "state_fingerprint": (
                self.state_fingerprint
            ),
            "checkpoint_identity": (
                self.checkpoint_identity
            ),
        }


def build_checkpoint_provenance(
    checkpoint: ExecutionCheckpoint,
) -> CheckpointProvenance:
    """Build immutable provenance for one checkpoint."""

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

    return CheckpointProvenance(
        authoritative_source=(
            CheckpointEngine.AUTHORITATIVE_SOURCE
        ),
        authoritative_state_path=(
            CheckpointEngine.AUTHORITATIVE_STATE_PATH
        ),
        checkpoint_id=(
            checkpoint.metadata.checkpoint_id
        ),
        created_at=(
            checkpoint.metadata.created_at
        ),
        schema_version=(
            checkpoint.metadata.schema_version
        ),
        state_fingerprint=(
            checkpoint.state_fingerprint
        ),
        checkpoint_identity=(
            identity.identity_key()
        ),
    )


__all__ = [
    "CheckpointProvenance",
    "build_checkpoint_provenance",
]