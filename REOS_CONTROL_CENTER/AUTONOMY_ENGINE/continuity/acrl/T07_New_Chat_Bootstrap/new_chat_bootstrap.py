"""ACRL T07 — New-Chat Bootstrap / Handoff.

Builds a compact deterministic restart payload from reconstructed
continuity context.

Authority remains:
    REOS_CONTROL_CENTER

T07 does not:
    - modify canonical state
    - create a second state store
    - invent project position
    - advance gates
    - complete subtasks
    - authorize execution
    - depend on chat history
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class BootstrapError(RuntimeError):
    """Base T07 bootstrap error."""


class BootstrapValidationError(BootstrapError):
    """Raised when bootstrap input is invalid."""


class BootstrapIntegrityError(BootstrapError):
    """Raised when bootstrap integrity verification fails."""


class BootstrapAuthorityError(BootstrapError):
    """Raised when authoritative continuity cannot be established."""


@dataclass(frozen=True)
class RestartPayload:
    """Minimal machine-readable payload required for a new session."""

    authority: str
    project_identity: str
    current_gate: str
    current_task: str
    current_subtask: str
    current_subtask_status: str
    first_valid_work_unit: str
    checkpoint_id: str
    resume_mode: str

    def to_dict(self) -> dict[str, str]:
        return {
            "authority": self.authority,
            "project_identity": self.project_identity,
            "current_gate": self.current_gate,
            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "current_subtask_status": self.current_subtask_status,
            "first_valid_work_unit": self.first_valid_work_unit,
            "checkpoint_id": self.checkpoint_id,
            "resume_mode": self.resume_mode,
        }


@dataclass(frozen=True)
class BootstrapContext:
    """Immutable machine-readable new-session bootstrap."""

    schema_version: str
    bootstrap_id: str
    authority: str

    project_dna: Mapping[str, Any]
    architecture_lock: Mapping[str, Any]
    execution_state: Mapping[str, Any]
    gate_continuity: Mapping[str, Any]
    dependency_authority: Mapping[str, Any]
    checkpoint: Mapping[str, Any]

    restart_payload: Mapping[str, Any]

    resume_mode: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
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
            "restart_payload": dict(
                self.restart_payload
            ),
            "resume_mode": self.resume_mode,
            "fingerprint": self.fingerprint,
        }

    def verify_integrity(self) -> bool:
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
            "restart_payload": dict(
                self.restart_payload
            ),
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

    def restart_payload_dict(self) -> dict[str, Any]:
        return dict(self.restart_payload)


class NewChatBootstrapEngine:
    """Build and validate deterministic new-session bootstrap."""

    SCHEMA_VERSION = "2.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    RESUME_MODE = "SAFE_AUTONOMOUS_RESUME"

    REQUIRED_EXECUTION_FIELDS = (
        "current_gate",
        "current_task",
        "current_subtask",
        "current_subtask_status",
    )

    def __init__(
        self,
        *,
        project_dna: Any,
        architecture_lock: Any,
        execution_state: Any,
        gate_continuity: Any,
        dependency_map: Any,
        checkpoint_engine: Any,
    ) -> None:
        self.project_dna = project_dna
        self.architecture_lock = architecture_lock
        self.execution_state = execution_state
        self.gate_continuity = gate_continuity
        self.dependency_map = dependency_map
        self.checkpoint_engine = checkpoint_engine

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
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
            return {
                key: getattr(value, key)
                for key in value.__dataclass_fields__
            }

        raise BootstrapValidationError(
            "Unsupported bootstrap projection type."
        )

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise BootstrapAuthorityError(
                f"{field_name} cannot be reconstructed."
            )

        return value.strip()

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
        checkpoint: Any,
    ) -> dict[str, Any]:
        if not hasattr(
            checkpoint,
            "verify_integrity",
        ):
            raise BootstrapValidationError(
                "Invalid checkpoint object."
            )

        if not checkpoint.verify_integrity():
            raise BootstrapIntegrityError(
                "Checkpoint integrity verification failed."
            )

        data = (
            checkpoint.to_dict()
            if hasattr(checkpoint, "to_dict")
            else dict(checkpoint)
        )

        if not isinstance(data, Mapping):
            raise BootstrapIntegrityError(
                "Checkpoint payload is not machine-readable."
            )

        return dict(data)

    def _validate_architecture(
        self,
        architecture_lock: Mapping[str, Any],
    ) -> None:
        status = str(
            architecture_lock.get(
                "status",
                architecture_lock.get(
                    "lock_status",
                    "",
                ),
            )
        ).upper()

        if status not in {
            "LOCKED",
            "FROZEN",
            "APPROVED",
            "APPROVED_NOT_FROZEN",
        }:
            raise BootstrapAuthorityError(
                "Architecture authority cannot be reconstructed."
            )

    def _validate_execution(
        self,
        execution_state: Mapping[str, Any],
    ) -> dict[str, str]:
        result: dict[str, str] = {}

        for field in self.REQUIRED_EXECUTION_FIELDS:
            value = execution_state.get(field)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise BootstrapAuthorityError(
                    f"Missing authoritative execution field: {field}"
                )

            result[field] = value.strip()

        return result

    def _build_restart_payload(
        self,
        *,
        project_dna: Mapping[str, Any],
        execution: Mapping[str, str],
        gate_continuity: Mapping[str, Any],
        dependency_authority: Mapping[str, Any],
        checkpoint: Mapping[str, Any],
    ) -> RestartPayload:
        project_identity = (
            project_dna.get("project")
            or project_dna.get("project_name")
            or project_dna.get("name")
        )

        project_identity = self._required_string(
            project_identity,
            "project_identity",
        )

        first_valid_work_unit = (
            gate_continuity.get(
                "first_valid_work_unit"
            )
            or dependency_authority.get(
                "first_valid_work_unit"
            )
        )

        if not first_valid_work_unit:
            current_gate = execution["current_gate"]
            current_subtask = execution["current_subtask"]

            first_valid_work_unit = (
                f"{current_gate}:{current_subtask}"
            )

        checkpoint_id = (
            checkpoint.get("checkpoint_id")
            or checkpoint.get("id")
        )

        checkpoint_id = self._required_string(
            checkpoint_id,
            "checkpoint_id",
        )

        return RestartPayload(
            authority=self.AUTHORITY,
            project_identity=project_identity,
            current_gate=execution["current_gate"],
            current_task=execution["current_task"],
            current_subtask=execution["current_subtask"],
            current_subtask_status=(
                execution["current_subtask_status"]
            ),
            first_valid_work_unit=(
                str(first_valid_work_unit)
            ),
            checkpoint_id=checkpoint_id,
            resume_mode=self.RESUME_MODE,
        )

    def build(
        self,
        *,
        bootstrap_id: str,
        checkpoint: Any,
    ) -> BootstrapContext:
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

        checkpoint_data = self._validate_checkpoint(
            checkpoint
        )

        self._validate_architecture(
            architecture_lock
        )

        execution = self._validate_execution(
            execution_state
        )

        restart_payload = (
            self._build_restart_payload(
                project_dna=project_dna,
                execution=execution,
                gate_continuity=gate_continuity,
                dependency_authority=(
                    dependency_authority
                ),
                checkpoint=checkpoint_data,
            )
        )

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "bootstrap_id": bootstrap_id,
            "authority": self.AUTHORITY,
            "project_dna": project_dna,
            "architecture_lock": architecture_lock,
            "execution_state": execution_state,
            "gate_continuity": gate_continuity,
            "dependency_authority": (
                dependency_authority
            ),
            "checkpoint": checkpoint_data,
            "restart_payload": (
                restart_payload.to_dict()
            ),
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
            dependency_authority=(
                dependency_authority
            ),
            checkpoint=checkpoint_data,
            restart_payload=(
                restart_payload.to_dict()
            ),
            resume_mode=self.RESUME_MODE,
            fingerprint=fingerprint,
        )

    @classmethod
    def validate_for_resume(
        cls,
        context: BootstrapContext,
    ) -> None:
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

        if context.resume_mode != cls.RESUME_MODE:
            raise BootstrapValidationError(
                "Unsafe resume mode."
            )

        if not context.project_dna:
            raise BootstrapAuthorityError(
                "Project identity context is missing."
            )

        if not context.execution_state:
            raise BootstrapAuthorityError(
                "Execution context is missing."
            )

        if not context.gate_continuity:
            raise BootstrapAuthorityError(
                "Gate continuity context is missing."
            )

        if not context.dependency_authority:
            raise BootstrapAuthorityError(
                "Dependency authority context is missing."
            )

        if not context.checkpoint:
            raise BootstrapIntegrityError(
                "Checkpoint context is missing."
            )

        restart = dict(
            context.restart_payload
        )

        required_restart_fields = (
            "authority",
            "project_identity",
            "current_gate",
            "current_task",
            "current_subtask",
            "current_subtask_status",
            "first_valid_work_unit",
            "checkpoint_id",
            "resume_mode",
        )

        for field in required_restart_fields:
            value = restart.get(field)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise BootstrapAuthorityError(
                    "Restart payload is incomplete: "
                    f"{field}"
                )

    @classmethod
    def resume_summary(
        cls,
        context: BootstrapContext,
    ) -> dict[str, str]:
        cls.validate_for_resume(context)

        restart = dict(
            context.restart_payload
        )

        return {
            "authority": context.authority,
            "bootstrap_id": context.bootstrap_id,
            "project_identity": restart[
                "project_identity"
            ],
            "current_gate": restart[
                "current_gate"
            ],
            "current_task": restart[
                "current_task"
            ],
            "current_subtask": restart[
                "current_subtask"
            ],
            "current_subtask_status": restart[
                "current_subtask_status"
            ],
            "first_valid_work_unit": restart[
                "first_valid_work_unit"
            ],
            "checkpoint_id": restart[
                "checkpoint_id"
            ],
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
    "RestartPayload",
]
