"""ACRL T06 — Checkpoint Engine.

Creates deterministic recovery checkpoints from authoritative REOS state.

Design principles:
    - REOS state remains the source of truth.
    - Checkpoints are recovery artifacts, not replacement state.
    - Checkpoints are immutable after creation.
    - Checkpoint identity is deterministic.
    - No gate/subtask transition is performed here.
    - No architecture mutation is performed here.
    - No ACRL __init__.py modification is required.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping


class CheckpointError(RuntimeError):
    """Base checkpoint-engine error."""


class CheckpointValidationError(CheckpointError):
    """Raised when checkpoint input is invalid."""


class CheckpointIntegrityError(CheckpointError):
    """Raised when checkpoint integrity validation fails."""


class CheckpointSourceError(CheckpointError):
    """Raised when the authoritative source is invalid."""


@dataclass(frozen=True)
class CheckpointMetadata:
    """Immutable metadata identifying a checkpoint."""

    checkpoint_id: str
    created_at: str
    schema_version: str = "1.0"


@dataclass(frozen=True)
class ExecutionCheckpoint:
    """Immutable recovery checkpoint."""

    metadata: CheckpointMetadata
    source: str
    state_snapshot: Mapping[str, Any]
    state_fingerprint: str
    checkpoint_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Return canonical serializable checkpoint data."""

        return {
            "schema_version": self.metadata.schema_version,
            "checkpoint_id": self.metadata.checkpoint_id,
            "created_at": self.metadata.created_at,
            "source": self.source,
            "state_snapshot": dict(self.state_snapshot),
            "state_fingerprint": self.state_fingerprint,
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
        }

    def verify_integrity(self) -> bool:
        """Verify that the checkpoint has not been altered."""

        expected_state_fingerprint = (
            CheckpointEngine.calculate_state_fingerprint(
                self.state_snapshot
            )
        )

        if expected_state_fingerprint != self.state_fingerprint:
            return False

        expected_checkpoint_fingerprint = (
            CheckpointEngine.calculate_checkpoint_fingerprint(
                checkpoint_id=self.metadata.checkpoint_id,
                source=self.source,
                state_fingerprint=self.state_fingerprint,
            )
        )

        return (
            expected_checkpoint_fingerprint
            == self.checkpoint_fingerprint
        )


class CheckpointEngine:
    """Build and validate deterministic REOS recovery checkpoints."""

    SCHEMA_VERSION = "1.0"
    AUTHORITATIVE_SOURCE = "REOS_STATE"
    AUTHORITATIVE_STATE_PATH = "data/state.json"

    REQUIRED_STATE_FIELDS = (
        "phase",
        "current_gate",
        "current_subtask",
        "status",
    )

    @staticmethod
    def _canonical_json(value: Any) -> str:
        """Serialize a value deterministically."""

        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise CheckpointValidationError(
                "Value cannot be serialized canonically."
            ) from exc

    @staticmethod
    def calculate_state_fingerprint(
        state: Mapping[str, Any],
    ) -> str:
        """Calculate deterministic SHA-256 fingerprint of state."""

        if not isinstance(state, Mapping):
            raise CheckpointValidationError(
                "State must be a mapping."
            )

        canonical = CheckpointEngine._canonical_json(dict(state))

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def calculate_checkpoint_fingerprint(
        *,
        checkpoint_id: str,
        source: str,
        state_fingerprint: str,
    ) -> str:
        """Calculate deterministic checkpoint fingerprint."""

        payload = {
            "checkpoint_id": checkpoint_id,
            "source": source,
            "state_fingerprint": state_fingerprint,
        }

        canonical = CheckpointEngine._canonical_json(payload)

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @classmethod
    def validate_authoritative_state(
        cls,
        state: Mapping[str, Any],
    ) -> None:
        """Validate the minimum authoritative state contract."""

        if not isinstance(state, Mapping):
            raise CheckpointSourceError(
                "Authoritative state must be a mapping."
            )

        for field in cls.REQUIRED_STATE_FIELDS:
            if field not in state:
                raise CheckpointSourceError(
                    f"Authoritative state missing required field: {field}"
                )

        for field in cls.REQUIRED_STATE_FIELDS:
            value = state[field]

            if not isinstance(value, str) or not value.strip():
                raise CheckpointSourceError(
                    f"Authoritative state field '{field}' "
                    "must be a non-empty string."
                )

    @classmethod
    def build_checkpoint(
        cls,
        state: Mapping[str, Any],
        *,
        checkpoint_id: str,
        created_at: str | None = None,
    ) -> ExecutionCheckpoint:
        """Create an immutable checkpoint from authoritative state."""

        if not isinstance(checkpoint_id, str):
            raise CheckpointValidationError(
                "checkpoint_id must be a string."
            )

        checkpoint_id = checkpoint_id.strip()

        if not checkpoint_id:
            raise CheckpointValidationError(
                "checkpoint_id must not be empty."
            )

        cls.validate_authoritative_state(state)

        if created_at is None:
            created_at = datetime.now(
                timezone.utc
            ).isoformat()

        if not isinstance(created_at, str) or not created_at.strip():
            raise CheckpointValidationError(
                "created_at must be a non-empty string."
            )

        state_snapshot = dict(state)

        state_fingerprint = cls.calculate_state_fingerprint(
            state_snapshot
        )

        checkpoint_fingerprint = (
            cls.calculate_checkpoint_fingerprint(
                checkpoint_id=checkpoint_id,
                source=cls.AUTHORITATIVE_SOURCE,
                state_fingerprint=state_fingerprint,
            )
        )

        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            created_at=created_at,
            schema_version=cls.SCHEMA_VERSION,
        )

        return ExecutionCheckpoint(
            metadata=metadata,
            source=cls.AUTHORITATIVE_SOURCE,
            state_snapshot=state_snapshot,
            state_fingerprint=state_fingerprint,
            checkpoint_fingerprint=checkpoint_fingerprint,
        )

    @classmethod
    def restore_state(
        cls,
        checkpoint: ExecutionCheckpoint,
    ) -> dict[str, Any]:
        """Return a validated state projection from a checkpoint."""

        if not isinstance(
            checkpoint,
            ExecutionCheckpoint,
        ):
            raise CheckpointValidationError(
                "checkpoint must be an ExecutionCheckpoint."
            )

        if not checkpoint.verify_integrity():
            raise CheckpointIntegrityError(
                "Checkpoint integrity verification failed."
            )

        cls.validate_authoritative_state(
            checkpoint.state_snapshot
        )

        return dict(checkpoint.state_snapshot)

    @classmethod
    def compare_checkpoint_state(
        cls,
        checkpoint: ExecutionCheckpoint,
        current_state: Mapping[str, Any],
    ) -> bool:
        """Determine whether checkpoint state matches current state."""

        if not checkpoint.verify_integrity():
            raise CheckpointIntegrityError(
                "Cannot compare an invalid checkpoint."
            )

        cls.validate_authoritative_state(current_state)

        current_fingerprint = cls.calculate_state_fingerprint(
            current_state
        )

        return (
            current_fingerprint
            == checkpoint.state_fingerprint
        )

    @classmethod
    def checkpoint_summary(
        cls,
        checkpoint: ExecutionCheckpoint,
    ) -> dict[str, str]:
        """Return a compact recovery summary."""

        if not checkpoint.verify_integrity():
            raise CheckpointIntegrityError(
                "Cannot summarize an invalid checkpoint."
            )

        state = checkpoint.state_snapshot

        return {
            "checkpoint_id": checkpoint.metadata.checkpoint_id,
            "phase": str(state["phase"]),
            "current_gate": str(state["current_gate"]),
            "current_subtask": str(state["current_subtask"]),
            "status": str(state["status"]),
            "state_fingerprint": checkpoint.state_fingerprint,
            "checkpoint_fingerprint": (
                checkpoint.checkpoint_fingerprint
            ),
        }


__all__ = [
    "CheckpointEngine",
    "CheckpointError",
    "CheckpointIntegrityError",
    "CheckpointMetadata",
    "CheckpointSourceError",
    "CheckpointValidationError",
    "ExecutionCheckpoint",
]