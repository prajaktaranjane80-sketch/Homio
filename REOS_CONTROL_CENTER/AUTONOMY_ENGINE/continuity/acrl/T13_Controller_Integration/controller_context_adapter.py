"""ACRL T13 — Control Center context adapter.

Bridges the canonical REOS Control Center state into the existing
read-only T13 ControllerStateView. The Control Center remains the
sole authority; this adapter only reconstructs a deterministic view.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .controller_integration import (
    ACRLContinuityView,
    ControllerIntegrationRequest,
    ControllerStateView,
    integrate_controller,
)


SCHEMA_VERSION = "1.0"
AUTHORITY = "REOS_CONTROL_CENTER"


class ControllerContextAdapterError(ValueError):
    """Base error for Control Center context adaptation."""


class ControllerContextAuthorityError(ControllerContextAdapterError):
    """Raised when Control Center authority is not preserved."""


class ControllerContextStateError(ControllerContextAdapterError):
    """Raised when canonical controller state is invalid."""


_REQUIRED_CONSTITUTION_FLAGS = (
    "single_source_of_truth",
    "autonomous_plan_is_authority",
    "next_step_must_come_from_control_center",
    "gate_subtasks_are_authoritative",
    "assistant_executes_current_subtask_only",
)


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ControllerContextStateError(
            f"{name} must be a mapping."
        )
    return value


def _require_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ControllerContextStateError(
            f"{name} must be a non-empty string."
        )
    return value


def _require_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ControllerContextStateError(
            f"{name} must be boolean."
        )
    return value


class ControllerContextAdapter:
    """Read-only adapter from canonical state.json data to T13."""

    SCHEMA_VERSION = SCHEMA_VERSION
    AUTHORITY = AUTHORITY

    @classmethod
    def controller_view_from_state(
        cls,
        state: Mapping[str, Any],
    ) -> ControllerStateView:
        """Build immutable controller evidence from canonical state."""

        root = _require_mapping(state, "state")
        constitution = _require_mapping(
            root.get("constitution"),
            "constitution",
        )
        execution = _require_mapping(
            root.get("execution"),
            "execution",
        )
        architecture = _require_mapping(
            root.get("architecture"),
            "architecture",
        )
        integrity = _require_mapping(
            root.get("integrity"),
            "integrity",
        )
        meta = _require_mapping(
            root.get("meta"),
            "meta",
        )
        phases = _require_mapping(
            root.get("phases"),
            "phases",
        )

        for flag in _REQUIRED_CONSTITUTION_FLAGS:
            if not _require_bool(
                constitution.get(flag),
                f"constitution.{flag}",
            ):
                raise ControllerContextAuthorityError(
                    f"Control Center authority contract is not active: {flag}"
                )

        state_hash = integrity.get("sha256")

        if (
            not isinstance(state_hash, str)
            or len(state_hash) != 64
        ):
            raise ControllerContextAuthorityError(
                "Verified canonical state SHA-256 is required."
            )

        current_gate = _require_string(
            execution.get("current_gate"),
            "execution.current_gate",
        )

        current_task = _require_string(
            execution.get("current_task"),
            "execution.current_task",
        )

        status = _require_string(
            execution.get("status"),
            "execution.status",
        )

        current_subtask = execution.get("current_subtask")

        gate_plans = root.get("gate_plans")

        if current_subtask is None and isinstance(
            gate_plans,
            Mapping,
        ):
            gate_plan = gate_plans.get(current_gate)

            if isinstance(gate_plan, Mapping):
                current_subtask = gate_plan.get(
                    "current_subtask"
                )

        if (
            current_subtask is not None
            and not isinstance(current_subtask, str)
        ):
            raise ControllerContextStateError(
                "execution.current_subtask must be a string or None."
            )

        architecture_locked = _require_bool(
            architecture.get("locked"),
            "architecture.locked",
        )

        checkpoint_id = execution.get("checkpoint_id")

        if (
            checkpoint_id is not None
            and not isinstance(checkpoint_id, str)
        ):
            raise ControllerContextStateError(
                "execution.checkpoint_id must be a string or None."
            )

        metadata = {
            "source": "REOS_CONTROL_CENTER/data/state.json",
            "control_center_version": meta.get(
                "control_center_version"
            ),
            "state_schema_version": meta.get(
                "schema_version"
            ),
            "product_version": meta.get("version"),
            "phase": phases.get("current"),
            "plan_authority": "REOS_CONTROL_CENTER",
        }

        metadata = {
            key: value
            for key, value in metadata.items()
            if isinstance(
                value,
                (str, int, float, bool),
            )
        }

        return ControllerStateView(
            current_gate=current_gate,
            current_subtask=current_subtask,
            current_task=current_task,
            status=status,
            state_hash=state_hash,
            architecture_locked=architecture_locked,
            authoritative=True,
            checkpoint_id=checkpoint_id,
            metadata=metadata,
        )

    @classmethod
    def build_request(
        cls,
        state: Mapping[str, Any],
        acrl: ACRLContinuityView,
    ) -> ControllerIntegrationRequest:
        """Build a T13 request without mutating Control Center state."""

        return ControllerIntegrationRequest(
            controller=cls.controller_view_from_state(state),
            acrl=acrl,
            expected_authority=cls.AUTHORITY,
        )

    @classmethod
    def integrate(
        cls,
        state: Mapping[str, Any],
        acrl: ACRLContinuityView,
    ):
        """Run existing T13 integration against canonical controller context."""

        return integrate_controller(
            cls.build_request(state, acrl)
        )


__all__ = [
    "AUTHORITY",
    "SCHEMA_VERSION",
    "ControllerContextAdapter",
    "ControllerContextAdapterError",
    "ControllerContextAuthorityError",
    "ControllerContextStateError",
]
