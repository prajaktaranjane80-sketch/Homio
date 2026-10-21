"""ACRL T07 — New-Chat Bootstrap / Handoff.

T07 reconstructs a compact restart payload from independently observed
continuity context. It does not change state or grant execution authority.
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


@dataclass(frozen=True, slots=True)
class RestartPayload:
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


@dataclass(frozen=True, slots=True)
class BootstrapContext:
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
            "architecture_lock": dict(self.architecture_lock),
            "execution_state": dict(self.execution_state),
            "gate_continuity": dict(self.gate_continuity),
            "dependency_authority": dict(self.dependency_authority),
            "checkpoint": dict(self.checkpoint),
            "restart_payload": dict(self.restart_payload),
            "resume_mode": self.resume_mode,
            "fingerprint": self.fingerprint,
        }

    def verify_integrity(self) -> bool:
        payload = {
            "schema_version": self.schema_version,
            "bootstrap_id": self.bootstrap_id,
            "authority": self.authority,
            "project_dna": dict(self.project_dna),
            "architecture_lock": dict(self.architecture_lock),
            "execution_state": dict(self.execution_state),
            "gate_continuity": dict(self.gate_continuity),
            "dependency_authority": dict(self.dependency_authority),
            "checkpoint": dict(self.checkpoint),
            "restart_payload": dict(self.restart_payload),
            "resume_mode": self.resume_mode,
        }
        return _fingerprint(payload) == self.fingerprint

    def restart_payload_dict(self) -> dict[str, Any]:
        return dict(self.restart_payload)


def _fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    def evaluate_fast_resume(
        *,
        manifest: Mapping[str, Any],
        live_snapshot: Mapping[str, Any],
        dependency_graph: Mapping[str, Any] | None = None,
        now=None,
    ):
        """Assess the cache before expensive repository discovery.

        Live HEAD, state.json SHA, branch and cleanliness must be obtained
        independently by the caller. The manifest itself never supplies
        current execution authority.
        """
        from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context.audit_resume_manifest import (
            assess_resume_manifest,
        )

        return assess_resume_manifest(
            manifest,
            live_snapshot,
            dependency_graph=dependency_graph,
            now=now,
        )

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
    def _required_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise BootstrapAuthorityError(
                f"{field_name} cannot be reconstructed."
            )
        return value.strip()

    @staticmethod
    def _validate_checkpoint(checkpoint: Any) -> dict[str, Any]:
        if (
            not hasattr(checkpoint, "verify_integrity")
            or not checkpoint.verify_integrity()
        ):
            raise BootstrapIntegrityError(
                "Checkpoint integrity verification failed."
            )

        try:
            data = (
                checkpoint.to_dict()
                if hasattr(checkpoint, "to_dict")
                else dict(checkpoint)
            )
        except (TypeError, ValueError) as exc:
            raise BootstrapIntegrityError(
                "Checkpoint payload is not machine-readable."
            ) from exc

        if not isinstance(data, Mapping):
            raise BootstrapIntegrityError(
                "Checkpoint payload is not machine-readable."
            )

        result = dict(data)
        NewChatBootstrapEngine._required_string(
            result.get("checkpoint_id") or result.get("id"),
            "checkpoint_id",
        )
        return result

    def _validate_architecture(
        self,
        architecture_lock: Mapping[str, Any],
    ) -> None:
        status = str(
            architecture_lock.get(
                "status",
                architecture_lock.get("lock_status", ""),
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
            if not isinstance(value, str) or not value.strip():
                raise BootstrapAuthorityError(
                    f"Missing authoritative execution field: {field}"
                )
            result[field] = value.strip()

        return result

    @classmethod
    def _validate_checkpoint_state_coherence(
        cls,
        *,
        checkpoint: Mapping[str, Any],
        execution: Mapping[str, str],
        gate_continuity: Mapping[str, Any],
    ) -> None:
        """Reject a valid-but-stale checkpoint that disagrees with live context."""
        if checkpoint.get("source") != "REOS_STATE":
            raise BootstrapAuthorityError(
                "Checkpoint source is not the canonical REOS state authority."
            )

        snapshot = checkpoint.get("state_snapshot")
        if not isinstance(snapshot, Mapping):
            raise BootstrapIntegrityError(
                "Checkpoint has no valid state snapshot."
            )

        checkpoint_fields = {
            "phase": snapshot.get("phase"),
            "current_gate": snapshot.get("current_gate"),
            "current_subtask": snapshot.get("current_subtask"),
            "status": snapshot.get("status"),
        }
        for field_name, value in checkpoint_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise BootstrapAuthorityError(
                    f"Checkpoint is missing authoritative field: {field_name}"
                )

        expected_fields = {
            "current_gate": execution["current_gate"],
            "current_subtask": execution["current_subtask"],
            "status": execution["current_subtask_status"],
        }
        for field_name, expected in expected_fields.items():
            if checkpoint_fields[field_name].strip() != expected:
                raise BootstrapAuthorityError(
                    f"Checkpoint {field_name} does not match the current "
                    "execution state."
                )

        # T06 checkpoints historically do not carry a separate current_task.
        # Bind that task ID to the canonical subtask when no explicit task
        # identity is present in the checkpoint snapshot.
        checkpoint_task = snapshot.get("current_task")
        execution_task = execution["current_task"]
        if checkpoint_task is not None:
            if (
                not isinstance(checkpoint_task, str)
                or not checkpoint_task.strip()
                or checkpoint_task.strip() != execution_task
            ):
                raise BootstrapAuthorityError(
                    "Checkpoint current_task does not match the current "
                    "execution state."
                )
        else:
            task_identity = execution_task.strip()
            for separator in (":", " — ", " - "):
                if separator in task_identity:
                    task_identity = task_identity.split(separator, 1)[0].strip()
                    break
            if task_identity != execution["current_subtask"]:
                raise BootstrapAuthorityError(
                    "Checkpoint cannot independently bind current_task to "
                    "current_subtask."
                )

        # Gate continuity is another independently supplied projection, not
        # a field to be inferred from the checkpoint itself.
        for field_name in ("current_gate", "current_subtask"):
            value = gate_continuity.get(field_name)
            if not isinstance(value, str) or not value.strip():
                raise BootstrapAuthorityError(
                    f"Gate-continuity authority is missing {field_name}."
                )
            if value.strip() != execution[field_name]:
                raise BootstrapAuthorityError(
                    f"Gate-continuity {field_name} conflicts with the "
                    "current execution state."
                )

        continuity_task = gate_continuity.get("current_task")
        if continuity_task is not None:
            if (
                not isinstance(continuity_task, str)
                or not continuity_task.strip()
                or continuity_task.strip() != execution_task
            ):
                raise BootstrapAuthorityError(
                    "Gate-continuity current_task conflicts with the "
                    "current execution state."
                )

    def _build_restart_payload(
        self,
        *,
        project_dna: Mapping[str, Any],
        execution: Mapping[str, str],
        gate_continuity: Mapping[str, Any],
        dependency_authority: Mapping[str, Any],
        checkpoint: Mapping[str, Any],
    ) -> RestartPayload:
        project_identity = self._required_string(
            project_dna.get("project")
            or project_dna.get("project_name")
            or project_dna.get("name"),
            "project_identity",
        )

        first_valid = (
            gate_continuity.get("first_valid_work_unit")
            or dependency_authority.get("first_valid_work_unit")
        )

        if not first_valid:
            first_valid = (
                f"{execution['current_gate']}:"
                f"{execution['current_subtask']}"
            )

        checkpoint_id = self._required_string(
            checkpoint.get("checkpoint_id") or checkpoint.get("id"),
            "checkpoint_id",
        )

        return RestartPayload(
            authority=self.AUTHORITY,
            project_identity=project_identity,
            current_gate=execution["current_gate"],
            current_task=execution["current_task"],
            current_subtask=execution["current_subtask"],
            current_subtask_status=execution["current_subtask_status"],
            first_valid_work_unit=self._required_string(
                first_valid,
                "first_valid_work_unit",
            ),
            checkpoint_id=checkpoint_id,
            resume_mode=self.RESUME_MODE,
        )

    def build(self, *, bootstrap_id: str, checkpoint: Any) -> BootstrapContext:
        if not isinstance(bootstrap_id, str) or not bootstrap_id.strip():
            raise BootstrapValidationError(
                "bootstrap_id cannot be empty."
            )

        bootstrap_id = bootstrap_id.strip()
        project_dna = self._as_dict(self.project_dna)
        architecture_lock = self._as_dict(self.architecture_lock)
        execution_state = self._as_dict(self.execution_state)
        gate_continuity = self._as_dict(self.gate_continuity)
        dependency_authority = self._as_dict(self.dependency_map)
        checkpoint_data = self._validate_checkpoint(checkpoint)

        self._validate_architecture(architecture_lock)
        execution = self._validate_execution(execution_state)
        self._validate_checkpoint_state_coherence(
            checkpoint=checkpoint_data,
            execution=execution,
            gate_continuity=gate_continuity,
        )

        restart = self._build_restart_payload(
            project_dna=project_dna,
            execution=execution,
            gate_continuity=gate_continuity,
            dependency_authority=dependency_authority,
            checkpoint=checkpoint_data,
        ).to_dict()

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
            "restart_payload": restart,
            "resume_mode": self.RESUME_MODE,
        }

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
            restart_payload=restart,
            resume_mode=self.RESUME_MODE,
            fingerprint=_fingerprint(payload),
        )

    @classmethod
    def validate_for_resume(cls, context: BootstrapContext) -> None:
        if not isinstance(context, BootstrapContext):
            raise BootstrapValidationError("Invalid bootstrap context.")

        if not context.verify_integrity():
            raise BootstrapIntegrityError(
                "Bootstrap fingerprint verification failed."
            )

        if context.authority != cls.AUTHORITY:
            raise BootstrapAuthorityError("Bootstrap authority mismatch.")

        if context.resume_mode != cls.RESUME_MODE:
            raise BootstrapValidationError("Unsafe resume mode.")

        if not context.project_dna:
            raise BootstrapAuthorityError(
                "Project identity context is missing."
            )

        if not context.execution_state:
            raise BootstrapAuthorityError(
                "Execution context is missing."
            )

        for field in cls.REQUIRED_EXECUTION_FIELDS:
            value = context.execution_state.get(field)
            if not isinstance(value, str) or not value.strip():
                raise BootstrapAuthorityError(
                    f"Execution context is incomplete: {field}"
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

        execution = {
            field: context.execution_state[field].strip()
            for field in cls.REQUIRED_EXECUTION_FIELDS
        }
        cls._validate_checkpoint_state_coherence(
            checkpoint=context.checkpoint,
            execution=execution,
            gate_continuity=context.gate_continuity,
        )

        restart = dict(context.restart_payload)
        required = (
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

        for field in required:
            value = restart.get(field)
            if not isinstance(value, str) or not value.strip():
                raise BootstrapAuthorityError(
                    f"Restart payload is incomplete: {field}"
                )

        if restart["authority"] != cls.AUTHORITY:
            raise BootstrapAuthorityError(
                "Restart payload authority mismatch."
            )

        if restart["resume_mode"] != cls.RESUME_MODE:
            raise BootstrapValidationError(
                "Restart payload has an unsafe resume mode."
            )

    @classmethod
    def resume_summary(
        cls,
        context: BootstrapContext,
    ) -> dict[str, str]:
        cls.validate_for_resume(context)
        restart = dict(context.restart_payload)

        return {
            "authority": context.authority,
            "bootstrap_id": context.bootstrap_id,
            "project_identity": restart["project_identity"],
            "current_gate": restart["current_gate"],
            "current_task": restart["current_task"],
            "current_subtask": restart["current_subtask"],
            "current_subtask_status": restart["current_subtask_status"],
            "first_valid_work_unit": restart["first_valid_work_unit"],
            "checkpoint_id": restart["checkpoint_id"],
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
