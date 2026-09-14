"""L3 canonical authority verification.

This module is intentionally NOT a second control plane.

Authority remains:
    REOS_CONTROL_CENTER
        -> data/state.json

This module only verifies that the existing authoritative Control Center
and canonical state are present, internally consistent, and usable.

It does not:
- own project state
- create or mutate state
- create a roadmap
- create a checkpoint engine
- execute mutations
- replace reos_control_center.py
- create an alternative authority
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
        """Verify that the canonical state is exactly data/state.json."""
        expected = (
            self.control_center_root / "data" / "state.json"
        ).resolve()

        return self.state_path == expected and self.state_path.is_file()

    def verify_state_integrity(self) -> bool:
        """Reuse the existing Control Center hash implementation."""
        if self._state is None:
            return False

        try:
            from reos_control_center import calculate_hash
        except ImportError:
            return False

        stored = (
            self._state
            .get("integrity", {})
            .get("sha256")
        )

        if not stored:
            return False

        return stored == calculate_hash(self._state)

    def verify_authority_declaration(self) -> bool:
        """Verify state.json declares itself as the canonical source."""
        if self._state is None:
            return False

        constitution = self._state.get("constitution", {})

        return (
            constitution.get("canonical_source")
            == "data/state.json"
            and constitution.get("single_source_of_truth") is True
        )

    def _resolve_execution_position(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        """Resolve the authoritative execution position from state.json.

        The Control Center state schema is authoritative.  L3 must not
        invent a parallel current-position schema.

        The preferred source is state["current"] when present.  If the
        canonical state stores the position through the authoritative
        gate/task structure instead, resolve it from that existing
        structure without mutating state.
        """
        if self._state is None:
            return None, None, None

        current = self._state.get("current")

        if isinstance(current, dict):
            gate = current.get("gate")
            task = current.get("task")
            subtask = current.get("subtask")

            if gate and task and subtask:
                return str(gate), str(task), str(subtask)

        gate_plans = self._state.get("gate_plans")

        if isinstance(gate_plans, dict):
            current_gate = self._state.get("current_gate")

            if current_gate and current_gate in gate_plans:
                gate_data = gate_plans[current_gate]

                if isinstance(gate_data, dict):
                    task = gate_data.get("current_task")
                    subtask = gate_data.get("current_subtask")

                    if task and subtask:
                        return (
                            str(current_gate),
                            str(task),
                            str(subtask),
                        )

        return None, None, None

    def verify_execution_position(self) -> bool:
        """Verify that the authoritative current execution position exists."""
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
    """Convenience wrapper around the read-only verifier."""
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
