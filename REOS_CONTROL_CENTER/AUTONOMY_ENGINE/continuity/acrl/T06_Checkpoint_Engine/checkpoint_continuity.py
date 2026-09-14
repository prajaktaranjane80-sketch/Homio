"""ACRL T06 — Checkpoint Continuity.

Read-only reconstruction of the latest safe recovery checkpoint.

Authoritative source:
    REOS_CONTROL_CENTER/data/state.json

This module:
    - finds the latest checkpoint
    - validates checkpoint identity
    - reconstructs checkpoint scope
    - validates completion evidence
    - reconstructs resumable position
    - reconstructs the interruption boundary

This module does NOT:
    - create checkpoints
    - modify checkpoints
    - modify state.json
    - advance gates
    - complete subtasks
    - authorize execution
    - create a second checkpoint store
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class CheckpointContinuityError(RuntimeError):
    """Base T06 continuity error."""


class CheckpointContinuitySourceError(
    CheckpointContinuityError
):
    """Authoritative checkpoint source cannot be loaded."""


class CheckpointContinuityIntegrityError(
    CheckpointContinuityError
):
    """Checkpoint structure or identity is invalid."""


class CheckpointContinuityConflictError(
    CheckpointContinuityError
):
    """Checkpoint conflicts with authoritative execution state."""


class CheckpointContinuityStatus(str, Enum):
    RESUMABLE = "RESUMABLE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CheckpointScope:
    """Immutable checkpoint scope."""

    phase: str
    gate_id: str
    task_id: str
    subtask_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "phase": self.phase,
            "gate": self.gate_id,
            "task": self.task_id,
            "subtask": self.subtask_id,
        }


@dataclass(frozen=True)
class CompletionEvidence:
    """Immutable completion evidence summary."""

    verified: bool
    evidence_ids: tuple[str, ...]
    evidence_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "evidence_ids": list(self.evidence_ids),
            "evidence_count": self.evidence_count,
        }


@dataclass(frozen=True)
class InterruptionBoundary:
    """Immutable point at which work was safely interrupted."""

    boundary_type: str
    resumable: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.boundary_type,
            "resumable": self.resumable,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CheckpointContinuity:
    """Complete immutable checkpoint continuity projection."""

    checkpoint_id: str
    checkpoint_created_at: str

    scope: CheckpointScope
    completion_evidence: CompletionEvidence
    resumable_position: str
    interruption_boundary: InterruptionBoundary

    status: CheckpointContinuityStatus

    checkpoint_fingerprint: str
    source_state_sha256: str

    def can_resume(self) -> bool:
        return self.status is CheckpointContinuityStatus.RESUMABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "checkpoint": {
                "id": self.checkpoint_id,
                "created_at": self.checkpoint_created_at,
                "fingerprint": self.checkpoint_fingerprint,
            },
            "scope": self.scope.to_dict(),
            "completion_evidence": (
                self.completion_evidence.to_dict()
            ),
            "resumable_position": self.resumable_position,
            "interruption_boundary": (
                self.interruption_boundary.to_dict()
            ),
            "resolution": {
                "status": self.status.value,
            },
            "authority": {
                "canonical_source": "data/state.json",
                "source_state_sha256": self.source_state_sha256,
            },
        }


class CheckpointContinuityReader:
    """Reconstruct latest checkpoint continuity from state.json."""

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            self.root = Path(__file__).resolve().parents[4]
        else:
            self.root = Path(control_center_root)

        self.state_path = self.root / "data" / "state.json"

    @staticmethod
    def _read_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise CheckpointContinuitySourceError(
                f"Authoritative state not found: {path}"
            )

        if not path.is_file():
            raise CheckpointContinuitySourceError(
                f"Authoritative state is not a file: {path}"
            )

        try:
            raw = path.read_text(encoding="utf-8-sig")
            state = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CheckpointContinuitySourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(state, dict):
            raise CheckpointContinuitySourceError(
                "Authoritative state must be a JSON object."
            )

        return state

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise CheckpointContinuityIntegrityError(
                f"{field_name} must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _string_tuple(
        value: Any,
        field_name: str,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise CheckpointContinuityIntegrityError(
                f"{field_name} must be a list."
            )

        result: list[str] = []

        for item in value:
            result.append(
                CheckpointContinuityReader._required_string(
                    item,
                    f"{field_name} entry",
                )
            )

        return tuple(result)

    @staticmethod
    def _sha256(path: Path) -> str:
        try:
            return hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        except OSError as exc:
            raise CheckpointContinuitySourceError(
                f"Unable to fingerprint state: {path}"
            ) from exc

    @staticmethod
    def _checkpoint_fingerprint(
        checkpoint: Mapping[str, Any],
    ) -> str:
        canonical = json.dumps(
            checkpoint,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _created_at_key(
        checkpoint: Mapping[str, Any],
    ) -> str:
        value = checkpoint.get("created_at")

        if value is None:
            value = checkpoint.get("time")

        if not isinstance(value, str) or not value.strip():
            raise CheckpointContinuityIntegrityError(
                "Checkpoint must contain created_at or time."
            )

        return value.strip()

    @staticmethod
    def _extract_checkpoint_scope(
        checkpoint: Mapping[str, Any],
    ) -> CheckpointScope:
        scope = checkpoint.get("scope")

        if isinstance(scope, Mapping):
            phase = scope.get("phase")
            gate_id = scope.get("gate")
            task_id = scope.get("task")
            subtask_id = scope.get("subtask")
        else:
            phase = checkpoint.get("phase")
            gate_id = checkpoint.get("current_gate")
            task_id = checkpoint.get("current_task")
            subtask_id = checkpoint.get("current_subtask")

        return CheckpointScope(
            phase=CheckpointContinuityReader._required_string(
                phase,
                "checkpoint.scope.phase",
            ),
            gate_id=CheckpointContinuityReader._required_string(
                gate_id,
                "checkpoint.scope.gate",
            ),
            task_id=CheckpointContinuityReader._required_string(
                task_id,
                "checkpoint.scope.task",
            ),
            subtask_id=CheckpointContinuityReader._required_string(
                subtask_id,
                "checkpoint.scope.subtask",
            ),
        )

    @staticmethod
    def _extract_evidence(
        checkpoint: Mapping[str, Any],
    ) -> CompletionEvidence:
        evidence = checkpoint.get("evidence")

        if isinstance(evidence, Mapping):
            verified = evidence.get("verified")
            evidence_ids = (
                evidence.get("ids")
                if "ids" in evidence
                else evidence.get("evidence_ids")
            )
        else:
            verified = checkpoint.get("evidence_verified")
            evidence_ids = checkpoint.get("evidence_ids")

        if not isinstance(verified, bool):
            raise CheckpointContinuityIntegrityError(
                "checkpoint completion evidence verification "
                "must be boolean."
            )

        ids = CheckpointContinuityReader._string_tuple(
            evidence_ids,
            "checkpoint.evidence_ids",
        )

        if verified and not ids:
            raise CheckpointContinuityIntegrityError(
                "Verified checkpoint must contain completion evidence."
            )

        return CompletionEvidence(
            verified=verified,
            evidence_ids=ids,
            evidence_count=len(ids),
        )

    @staticmethod
    def _extract_boundary(
        checkpoint: Mapping[str, Any],
    ) -> InterruptionBoundary:
        boundary = checkpoint.get(
            "interruption_boundary"
        )

        if isinstance(boundary, Mapping):
            boundary_type = boundary.get("type")
            resumable = boundary.get("resumable")
            reason = boundary.get("reason")
        else:
            boundary_type = checkpoint.get(
                "boundary_type"
            )
            resumable = checkpoint.get(
                "resumable",
            )
            reason = checkpoint.get(
                "interruption_reason",
            )

        if not isinstance(resumable, bool):
            raise CheckpointContinuityIntegrityError(
                "checkpoint interruption boundary resumable "
                "flag must be boolean."
            )

        return InterruptionBoundary(
            boundary_type=CheckpointContinuityReader._required_string(
                boundary_type,
                "checkpoint.interruption_boundary.type",
            ),
            resumable=resumable,
            reason=CheckpointContinuityReader._required_string(
                reason,
                "checkpoint.interruption_boundary.reason",
            ),
        )

    @staticmethod
    def _extract_checkpoint_id(
        checkpoint: Mapping[str, Any],
    ) -> str:
        value = checkpoint.get("checkpoint_id")

        if value is None:
            value = checkpoint.get("id")

        return CheckpointContinuityReader._required_string(
            value,
            "checkpoint.id",
        )

    def _latest_checkpoint(
        self,
        state: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        raw = state.get("checkpoints")

        if raw is None:
            raise CheckpointContinuitySourceError(
                "state.checkpoints is missing."
            )

        if not isinstance(raw, list):
            raise CheckpointContinuityIntegrityError(
                "state.checkpoints must be a list."
            )

        if not raw:
            raise CheckpointContinuityConflictError(
                "No recovery checkpoint exists."
            )

        checkpoints: list[Mapping[str, Any]] = []

        for index, checkpoint in enumerate(raw):
            if not isinstance(checkpoint, Mapping):
                raise CheckpointContinuityIntegrityError(
                    f"checkpoints[{index}] must be an object."
                )

            self._checkpoint_id_for_validation(
                checkpoint,
                index,
            )

            checkpoints.append(checkpoint)

        checkpoints.sort(
            key=self._created_at_key,
        )

        return checkpoints[-1]

    def _checkpoint_id_for_validation(
        self,
        checkpoint: Mapping[str, Any],
        index: int,
    ) -> str:
        checkpoint_id = self._extract_checkpoint_id(
            checkpoint
        )

        if not checkpoint_id:
            raise CheckpointContinuityIntegrityError(
                f"checkpoints[{index}] has empty identity."
            )

        return checkpoint_id

    def reconstruct(self) -> CheckpointContinuity:
        """Reconstruct the latest safe checkpoint."""

        state = self._read_state(self.state_path)

        checkpoint = self._latest_checkpoint(state)

        checkpoint_id = self._extract_checkpoint_id(
            checkpoint
        )
        created_at = self._created_at_key(
            checkpoint
        )

        scope = self._extract_checkpoint_scope(
            checkpoint
        )

        completion_evidence = self._extract_evidence(
            checkpoint
        )

        boundary = self._extract_boundary(
            checkpoint
        )

        resumable_position = (
            f"{scope.gate_id}:{scope.task_id}:{scope.subtask_id}"
        )

        conflicts: list[str] = []

        if not completion_evidence.verified:
            conflicts.append(
                "Checkpoint completion evidence is not verified."
            )

        if not boundary.resumable:
            conflicts.append(
                "Checkpoint interruption boundary is not resumable."
            )

        execution = state.get("execution")

        if not isinstance(execution, Mapping):
            raise CheckpointContinuityIntegrityError(
                "state.execution must be an object."
            )

        current_gate = execution.get("current_gate")
        current_task = execution.get("current_task")

        if (
            isinstance(current_gate, str)
            and current_gate.strip()
            and current_gate.strip() != scope.gate_id
        ):
            conflicts.append(
                "Checkpoint gate differs from current authoritative gate."
            )

        if (
            isinstance(current_task, str)
            and current_task.strip()
            and current_task.strip() != scope.task_id
        ):
            conflicts.append(
                "Checkpoint task differs from current authoritative task."
            )

        status = (
            CheckpointContinuityStatus.BLOCKED
            if conflicts
            else CheckpointContinuityStatus.RESUMABLE
        )

        fingerprint = self._checkpoint_fingerprint(
            checkpoint
        )

        return CheckpointContinuity(
            checkpoint_id=checkpoint_id,
            checkpoint_created_at=created_at,
            scope=scope,
            completion_evidence=completion_evidence,
            resumable_position=resumable_position,
            interruption_boundary=boundary,
            status=status,
            checkpoint_fingerprint=fingerprint,
            source_state_sha256=self._sha256(
                self.state_path
            ),
        )


def reconstruct_checkpoint_continuity(
    control_center_root: Path | str | None = None,
) -> CheckpointContinuity:
    """Convenience API for checkpoint continuity."""

    return CheckpointContinuityReader(
        control_center_root
    ).reconstruct()


__all__ = [
    "CheckpointContinuity",
    "CheckpointContinuityConflictError",
    "CheckpointContinuityError",
    "CheckpointContinuityIntegrityError",
    "CheckpointContinuityReader",
    "CheckpointContinuitySourceError",
    "CheckpointContinuityStatus",
    "CheckpointScope",
    "CompletionEvidence",
    "InterruptionBoundary",
    "reconstruct_checkpoint_continuity",
]
