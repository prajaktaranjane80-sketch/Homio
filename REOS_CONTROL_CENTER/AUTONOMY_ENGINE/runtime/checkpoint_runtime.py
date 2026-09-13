from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CheckpointIntent:
    checkpoint_id: str
    mission_id: str
    note: str
    evidence: dict[str, Any]


class CheckpointRuntime:
    """
    Build a checkpoint intent.

    The actual Control Center checkpoint remains outside this module.
    """

    def prepare(
        self,
        *,
        checkpoint_id: str,
        mission_id: str,
        note: str,
        evidence: dict[str, Any],
    ) -> CheckpointIntent:
        if not checkpoint_id.strip():
            raise ValueError("checkpoint_id required")

        if not mission_id.strip():
            raise ValueError("mission_id required")

        if not note.strip():
            raise ValueError("note required")

        return CheckpointIntent(
            checkpoint_id=checkpoint_id,
            mission_id=mission_id,
            note=note.strip(),
            evidence=dict(evidence),
        )
