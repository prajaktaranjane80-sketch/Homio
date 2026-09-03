"""ACRL T07 — New-Chat Bootstrap / Handoff.

Additive-only continuity layer.

Consumes T01-T06 read-only and creates a compact, deterministic,
machine-readable handoff that allows a new AI/operator session to
reconstruct the current REOS execution context without relying on
chat history.

Important:
    - T01-T06 are never modified.
    - __init__.py is never modified.
    - REOS_CONTROL_CENTER remains authoritative.
    - This module does not mutate execution state.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .architecture_lock import (
    ArchitectureLock,
    ArchitectureNotLockedError,
)
from .checkpoint_engine import (
    CheckpointEngine,
    ExecutionCheckpoint,
)
from .dependency_authority_map import (
    DependencyAuthorityMap,
    AuthorityConflictError,
    build_dependency_authority_map,
)
from .gate_subtask_continuity import (
    GateSubtaskContinuity,
)
from .project_dna import (
    ProjectDNA,
)
from .state_reconstruction import (
    ExecutionStateSnapshot,
)


class BootstrapError(RuntimeError):
    """Base T07 bootstrap error."""


class BootstrapValidationError(BootstrapError):
    """Raised when bootstrap input is invalid."""


class BootstrapIntegrityError(BootstrapError):
    """Raised when bootstrap integrity verification fails."""


class BootstrapAuthorityError(BootstrapError):
    """Raised when authoritative continuity cannot be established."""


@dataclass(frozen=True)
class BootstrapContext:
    """Immutable machine-readable new-chat handoff."""

    schema_version: str
    bootstrap_id: str
    authority: str
    project_dna: Mapping[str, Any]
    architecture_lock: Mapping[str, Any]
    execution_state: Mapping[str, Any]
    gate_continuity: Mapping[str, Any]
    dependency_authority: Mapping[str, Any]
    checkpoint: Mapping[str, Any]
    resume_mode: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Return the complete handoff payload."""

        return {
            "schema_version": self.schema_version,
            "bootstrap_id": self.bootstrap_id,
            "authority": self.authority,
            "project_dna": dict(self.project_dna),
            "architecture_lock": dict(
                self.architecture_lock
            ),
            "execution_state": dict(
                self.execution_state
            ),
            "gate_continuity": dict(
                self.gate_continuity
            ),
            "dependency_authority": dict(
                self.dependency_authority
            ),
            "checkpoint": dict(self.checkpoint),
            "resume_mode": self.resume_mode,
            "fingerprint": self.fingerprint,
        }

    def verify_integrity(self) -> bool:
        """Verify the deterministic bootstrap fingerprint."""

        payload = {
            "schema_version": self.schema_version,
            "bootstrap_id": self.bootstrap_id,
            "authority": self.authority,
            "project_dna": dict(self.project_dna),
            "architecture_lock": dict(
                self.architecture_lock
            ),
            "execution_state": dict(
                self.execution_state
            ),
            "gate_continuity": dict(
                self.gate_continuity
            ),
            "dependency_authority": dict(
                self.dependency_authority
            ),
            "checkpoint": dict(self.checkpoint),
            "resume_mode": self.resume_mode,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        expected = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return expected == self.fingerprint


class NewChatBootstrapEngine:
    """Build and validate autonomous new-chat handoffs."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    RESUME_MODE = "SAFE_AUTONOMOUS_RESUME"

    def __init__(
        self,
        *,
        project_dna: ProjectDNA,
        architecture_lock: ArchitectureLock,
        execution_state: ExecutionStateSnapshot,
        gate_continuity: GateSubtaskContinuity,
        dependency_map: DependencyAuthorityMap,
        checkpoint_engine: CheckpointEngine,
    ) -> None:
        self.project_dna = project_dna
        self.architecture_lock = architecture_lock
        self.execution_state = execution_state
        self.gate_continuity = gate_continuity
        self.dependency_map = dependency_map
        self.checkpoint_engine = checkpoint_engine

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        """Convert an ACRL object to a serializable dictionary."""

        if hasattr(value, "to_dict"):
            result = value.to_dict()

            if not isinstance(result, Mapping):
                raise BootstrapValidationError(
                    "to_dict() must return a mapping."
                )

            return dict(result)

        if isinstance(value, Mapping):
            return dict(value)

        if hasattr(value, "__dataclass_fields__"):
            try:
                return {
                    key: getattr(value, key)
                    for key in value.__dataclass_fields__
                }
            except Exception as exc:
                raise BootstrapValidationError(
                    "Unable to serialize dataclass projection."
                ) from exc

        raise BootstrapValidationError(
            "Unsupported ACRL projection type."
        )

    @classmethod
    def _fingerprint(
        cls,
        payload: Mapping[str, Any],
    ) -> str:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _validate_checkpoint(
        checkpoint: ExecutionCheckpoint,
    ) -> None:
        if not isinstance(
            checkpoint,
            ExecutionCheckpoint,
        ):
            raise BootstrapValidationError(
                "Invalid checkpoint type."
            )

        if not checkpoint.verify_integrity():
            raise BootstrapIntegrityError(
                "Checkpoint integrity verification failed."
            )

    def _validate_architecture_lock(self) -> None:
        """Ensure architecture is actually locked."""

        architecture = self._as_dict(
            self.architecture_lock
        )

        status = str(
            architecture.get(
                "status",
                architecture.get(
                    "lock_status",
                    "",
                ),
            )
        ).upper()

        if status not in {
            "LOCKED",
            "FROZEN",
            "APPROVED",
        }:
            raise BootstrapAuthorityError(
                "Architecture is not locked/frozen."
            )

    def _validate_dependency_authority(self) -> None:
        """Ensure ACRL has a valid authoritative dependency map."""

        if not isinstance(
            self.dependency_map,
            DependencyAuthorityMap,
        ):
            raise BootstrapAuthorityError(
                "Invalid dependency authority map."
            )

        try:
            data = self._as_dict(
                self.dependency_map
            )
        except BootstrapValidationError as exc:
            raise BootstrapAuthorityError(
                "Dependency authority map cannot be serialized."
            ) from exc

        canonical = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        if not canonical:
            raise BootstrapAuthorityError(
                "Dependency authority map is empty."
            )

        if hasattr(
            self.dependency_map,
            "verify_integrity",
        ):
            if not self.dependency_map.verify_integrity():
                raise BootstrapIntegrityError(
                    "Dependency authority map integrity failed."
                )

    def build(
        self,
        *,
        bootstrap_id: str,
        checkpoint: ExecutionCheckpoint,
    ) -> BootstrapContext:
        """Build a complete safe new-chat handoff."""

        if not isinstance(
            bootstrap_id,
            str,
        ):
            raise BootstrapValidationError(
                "bootstrap_id must be a string."
            )

        bootstrap_id = bootstrap_id.strip()

        if not bootstrap_id:
            raise BootstrapValidationError(
                "bootstrap_id cannot be empty."
            )

        self._validate_checkpoint(
            checkpoint
        )

        self._validate_architecture_lock()

        self._validate_dependency_authority()

        project_dna = self._as_dict(
            self.project_dna
        )

        architecture_lock = self._as_dict(
            self.architecture_lock
        )

        execution_state = self._as_dict(
            self.execution_state
        )

        gate_continuity = self._as_dict(
            self.gate_continuity
        )

        dependency_authority = self._as_dict(
            self.dependency_map
        )

        checkpoint_data = checkpoint.to_dict()

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "bootstrap_id": bootstrap_id,
            "authority": self.AUTHORITY,
            "project_dna": project_dna,
            "architecture_lock": architecture_lock,
            "execution_state": execution_state,
            "gate_continuity": gate_continuity,
            "dependency_authority": dependency_authority,
            "checkpoint": checkpoint_data,
            "resume_mode": self.RESUME_MODE,
        }

        fingerprint = self._fingerprint(
            payload
        )

        return BootstrapContext(
            schema_version=self.SCHEMA_VERSION,
            bootstrap_id=bootstrap_id,
            authority=self.AUTHORITY,
            project_dna=project_dna,
            architecture_lock=architecture_lock,
            execution_state=execution_state,
            gate_continuity=gate_continuity,
            dependency_authority=dependency_authority,
            checkpoint=checkpoint_data,
            resume_mode=self.RESUME_MODE,
            fingerprint=fingerprint,
        )

    @classmethod
    def validate_for_resume(
        cls,
        context: BootstrapContext,
    ) -> None:
        """Fail closed when a handoff is unsafe."""

        if not isinstance(
            context,
            BootstrapContext,
        ):
            raise BootstrapValidationError(
                "Invalid bootstrap context."
            )

        if not context.verify_integrity():
            raise BootstrapIntegrityError(
                "Bootstrap fingerprint verification failed."
            )

        if context.authority != cls.AUTHORITY:
            raise BootstrapAuthorityError(
                "Bootstrap authority mismatch."
            )

        if (
            context.resume_mode
            != cls.RESUME_MODE
        ):
            raise BootstrapValidationError(
                "Unsafe resume mode."
            )

        if not context.checkpoint:
            raise BootstrapIntegrityError(
                "Missing checkpoint."
            )

        architecture = dict(
            context.architecture_lock
        )

        status = str(
            architecture.get(
                "status",
                architecture.get(
                    "lock_status",
                    "",
                ),
            )
        ).upper()

        if status not in {
            "LOCKED",
            "FROZEN",
            "APPROVED",
        }:
            raise BootstrapAuthorityError(
                "Architecture lock is not valid for resume."
            )

    @classmethod
    def resume_summary(
        cls,
        context: BootstrapContext,
    ) -> dict[str, str]:
        """Return the minimum safe context required to resume."""

        cls.validate_for_resume(
            context
        )

        execution = dict(
            context.execution_state
        )

        gate = dict(
            context.gate_continuity
        )

        current_gate = str(
            execution.get(
                "current_gate",
                gate.get(
                    "current_gate",
                    "",
                ),
            )
        )

        current_subtask = str(
            execution.get(
                "current_subtask",
                gate.get(
                    "current_subtask",
                    "",
                ),
            )
        )

        if not current_gate:
            raise BootstrapAuthorityError(
                "Current gate cannot be reconstructed."
            )

        if not current_subtask:
            raise BootstrapAuthorityError(
                "Current subtask cannot be reconstructed."
            )

        return {
            "authority": context.authority,
            "bootstrap_id": context.bootstrap_id,
            "current_gate": current_gate,
            "current_subtask": current_subtask,
            "resume_mode": context.resume_mode,
            "fingerprint": context.fingerprint,
        }


__all__ = [
    "BootstrapAuthorityError",
    "BootstrapContext",
    "BootstrapError",
    "BootstrapIntegrityError",
    "BootstrapValidationError",
    "NewChatBootstrapEngine",
]