"""L3 canonical authority verification.

This module is NOT a second control plane.

Authority remains:
    REOS_CONTROL_CENTER
        -> data/state.json

This module only verifies the existing authoritative Control Center
and canonical state. It does not own, create, mutate, or replace state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CanonicalAuthorityResult:
    allowed: bool
    reason: str
    state_path: Path
    current_gate: str | None = None
    current_task: str | None = None
    current_subtask: str | None = None


class CanonicalAuthorityVerifier:
    """Read-only verifier for the existing REOS Control Center authority."""

    def __init__(
        self,
        control_center_root: Path,
        state: dict[str, Any] | None = None,
    ) -> None:
        self.control_center_root = Path(control_center_root).resolve()
        self.state_path = (
            self.control_center_root / "data" / "state.json"
        ).resolve()
        self._state = state

    def verify_state_path(self) -> bool:
        """Canonical state must be exactly data/state.json."""
        expected = (
            self.control_center_root / "data" / "state.json"
        ).resolve()

        return (
            self.state_path == expected
            and self.state_path.is_file()
        )

    def verify_state_integrity(self) -> bool:
        """Reuse the existing Control Center hash implementation."""
        if self._state is None:
            return False

        try:
            from reos_control_center import calculate_hash
        except ImportError:
            return False

        integrity = self._state.get("integrity")

        if not isinstance(integrity, dict):
            return False

        stored = integrity.get("sha256")

        if not isinstance(stored, str) or not stored.strip():
            return False

        return stored == calculate_hash(self._state)

    def verify_authority_declaration(self) -> bool:
        """Verify the canonical authority declaration."""
        if self._state is None:
            return False

        constitution = self._state.get("constitution")

        if not isinstance(constitution, dict):
            return False

        return (
            constitution.get("canonical_source")
            == "data/state.json"
            and constitution.get("single_source_of_truth") is True
        )

    def _resolve_execution_position(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        """Resolve the current position from the canonical state schema.

        The existing Control Center schema is authoritative:

            state["execution"]["current_gate"]
            state["execution"]["current_task"]

        The current subtask is resolved from the authoritative gate plan.
        No parallel ``current`` state structure is created.
        """
        if self._state is None:
            return None, None, None

        execution = self._state.get("execution")

        if not isinstance(execution, dict):
            return None, None, None

        gate = execution.get("current_gate")
        task = execution.get("current_task")

        if not gate or not task:
            return None, None, None

        gate_plans = self._state.get("gate_plans")

        if not isinstance(gate_plans, dict):
            return None, None, None

        gate_data = gate_plans.get(gate)

        if not isinstance(gate_data, dict):
            return None, None, None

        subtask = gate_data.get("current_subtask")

        if not subtask:
            return None, None, None

        return str(gate), str(task), str(subtask)

    def verify_execution_position(self) -> bool:
        """Verify the authoritative execution position."""
        gate, task, subtask = self._resolve_execution_position()

        return bool(gate and task and subtask)

    def verify(self) -> CanonicalAuthorityResult:
        """Perform read-only L3 canonical authority verification."""

        if not self.verify_state_path():
            return CanonicalAuthorityResult(
                allowed=False,
                reason="CANONICAL_STATE_PATH_INVALID",
                state_path=self.state_path,
            )

        if self._state is None:
            return CanonicalAuthorityResult(
                allowed=False,
                reason="CANONICAL_STATE_NOT_LOADED",
                state_path=self.state_path,
            )

        if not self.verify_state_integrity():
            return CanonicalAuthorityResult(
                allowed=False,
                reason="CANONICAL_STATE_INTEGRITY_FAILURE",
                state_path=self.state_path,
            )

        if not self.verify_authority_declaration():
            return CanonicalAuthorityResult(
                allowed=False,
                reason="CANONICAL_AUTHORITY_DECLARATION_INVALID",
                state_path=self.state_path,
            )

        gate, task, subtask = self._resolve_execution_position()

        if not (gate and task and subtask):
            return CanonicalAuthorityResult(
                allowed=False,
                reason="AUTHORITATIVE_EXECUTION_POSITION_INVALID",
                state_path=self.state_path,
            )

        return CanonicalAuthorityResult(
            allowed=True,
            reason="CANONICAL_AUTHORITY_VERIFIED",
            state_path=self.state_path,
            current_gate=gate,
            current_task=task,
            current_subtask=subtask,
        )


def verify_canonical_authority(
    control_center_root: Path,
    state: dict[str, Any],
) -> CanonicalAuthorityResult:
    """Convenience wrapper for read-only L3 verification."""
    verifier = CanonicalAuthorityVerifier(
        control_center_root=control_center_root,
        state=state,
    )
    return verifier.verify()


__all__ = [
    "CanonicalAuthorityResult",
    "CanonicalAuthorityVerifier",
    "verify_canonical_authority",
]
