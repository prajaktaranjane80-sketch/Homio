"""ACRL T06 — deterministic checkpoint identity."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .checkpoint_engine import ExecutionCheckpoint


@dataclass(frozen=True)
class CheckpointIdentity:
    """Immutable deterministic identity of one checkpoint."""

    schema_version: str
    checkpoint_id: str
    source: str
    state_fingerprint: str
    canonical_sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_id": self.checkpoint_id,
            "source": self.source,
            "state_fingerprint": self.state_fingerprint,
            "canonical_sha256": self.canonical_sha256,
        }

    def identity_key(self) -> str:
        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


def build_checkpoint_identity(
    checkpoint: ExecutionCheckpoint,
) -> CheckpointIdentity:
    """Build deterministic identity from an immutable checkpoint."""

    if not isinstance(checkpoint, ExecutionCheckpoint):
        raise TypeError(
            "checkpoint must be ExecutionCheckpoint."
        )

    payload = {
        "schema_version": checkpoint.metadata.schema_version,
        "checkpoint_id": checkpoint.metadata.checkpoint_id,
        "source": checkpoint.source,
        "state_fingerprint": checkpoint.state_fingerprint,
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return CheckpointIdentity(
        schema_version=(
            checkpoint.metadata.schema_version
        ),
        checkpoint_id=(
            checkpoint.metadata.checkpoint_id
        ),
        source=checkpoint.source,
        state_fingerprint=(
            checkpoint.state_fingerprint
        ),
        canonical_sha256=digest,
    )


__all__ = [
    "CheckpointIdentity",
    "build_checkpoint_identity",
]