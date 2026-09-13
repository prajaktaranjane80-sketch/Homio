"""
REOS Diagnostic Probes
======================

Small, isolated, read-only probes.

Important:
    These probes inspect the system.
    They do not repair it.
    They do not execute business actions.
    They do not mutate state.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .diagnostic_models import (
    DiagnosticCheck,
    DiagnosticEvidence,
    DiagnosticPosition,
    STATUS_BLOCKED,
    STATUS_PASS,
)


class DiagnosticProbeSet:
    """
    Read-only probe collection for the existing REOS architecture.
    """

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    @property
    def control_center(self) -> Path:
        return self.project_root / "REOS_CONTROL_CENTER"

    @property
    def state_file(self) -> Path:
        return (
            self.control_center
            / "data"
            / "state.json"
        )

    @property
    def autonomy_engine(self) -> Path:
        return (
            self.control_center
            / "AUTONOMY_ENGINE"
        )

    @property
    def acrl(self) -> Path:
        return (
            self.autonomy_engine
            / "continuity"
            / "acrl"
        )

    @property
    def runtime(self) -> Path:
        return (
            self.autonomy_engine
            / "runtime"
        )

    # ------------------------------------------------------------------
    # Control Center
    # ------------------------------------------------------------------

    def control_center_check(self) -> DiagnosticCheck:
        if not self.control_center.is_dir():
            return self._blocked(
                "CONTROL_CENTER",
                "Control Center directory unavailable",
                "Restore REOS_CONTROL_CENTER",
            )

        if not self.state_file.is_file():
            return self._blocked(
                "CONTROL_CENTER",
                "Canonical state.json unavailable",
                "Restore REOS_CONTROL_CENTER/data/state.json",
            )

        return self._pass(
            "CONTROL_CENTER",
            "Canonical Control Center surface available",
            (
                DiagnosticEvidence(
                    "filesystem",
                    str(self.control_center),
                ),
            ),
        )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def load_state(self) -> dict[str, Any] | None:
        if not self.state_file.is_file():
            return None

        try:
            with self.state_file.open(
                "r",
                encoding="utf-8",
            ) as handle:
                value = json.load(handle)
        except (
            OSError,
            ValueError,
            json.JSONDecodeError,
        ):
            return None

        if not isinstance(value, dict):
            return None

        return value

    def state_check(
        self,
        state: dict[str, Any] | None,
    ) -> DiagnosticCheck:
        if state is None:
            return self._blocked(
                "STATE",
                "Canonical state cannot be reconstructed",
                "Repair canonical state before autonomous execution",
            )

        return self._pass(
            "STATE",
            "Canonical state is readable",
            (
                DiagnosticEvidence(
                    "state",
                    str(self.state_file),
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Architecture
    # ------------------------------------------------------------------

    def architecture_check(
        self,
        state: dict[str, Any] | None,
    ) -> DiagnosticCheck:
        if state is None:
            return self._blocked(
                "ARCHITECTURE",
                "State unavailable for architecture context",
                "Repair STATE first",
            )

        return self._pass(
            "ARCHITECTURE",
            "Architecture authority remains external to diagnostics",
            (
                DiagnosticEvidence(
                    "authority",
                    "approved/frozen HOMIO/REOS architecture",
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Autonomy Engine
    # ------------------------------------------------------------------

    def autonomy_engine_check(self) -> DiagnosticCheck:
        if not self.autonomy_engine.is_dir():
            return self._blocked(
                "AUTONOMY_ENGINE",
                "AUTONOMY_ENGINE unavailable",
                "Restore AUTONOMY_ENGINE",
            )

        return self._pass(
            "AUTONOMY_ENGINE",
            "Autonomy engine surface available",
            (
                DiagnosticEvidence(
                    "filesystem",
                    str(self.autonomy_engine),
                ),
            ),
        )

    # ------------------------------------------------------------------
    # ACRL
    # ------------------------------------------------------------------

    def acrl_check(self) -> DiagnosticCheck:
        if not self.acrl.is_dir():
            return self._blocked(
                "ACRL",
                "ACRL continuity layer unavailable",
                "Restore AUTONOMY_ENGINE/continuity/acrl",
            )

        return self._pass(
            "ACRL",
            "ACRL continuity surface available",
            (
                DiagnosticEvidence(
                    "filesystem",
                    str(self.acrl),
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def runtime_check(self) -> DiagnosticCheck:
        if not self.runtime.is_dir():
            return self._blocked(
                "RUNTIME",
                "Runtime directory unavailable",
                "Synchronize the canonical runtime tree",
            )

        modules = tuple(
            self.runtime.glob("*.py")
        )

        if not modules:
            return self._blocked(
                "RUNTIME",
                "Runtime contains no Python modules",
                "Synchronize runtime implementation",
            )

        return self._pass(
            "RUNTIME",
            "Runtime implementation surface available",
            (
                DiagnosticEvidence(
                    "runtime",
                    str(self.runtime),
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Mission Cycle
    # ------------------------------------------------------------------

    def mission_cycle_check(self) -> DiagnosticCheck:
        path = self.runtime / "mission_cycle.py"

        if not path.is_file():
            return self._blocked(
                "MISSION_CYCLE",
                "Mission cycle runtime unavailable",
                "Restore runtime/mission_cycle.py",
            )

        return self._pass(
            "MISSION_CYCLE",
            "Mission cycle surface available",
            (
                DiagnosticEvidence(
                    "runtime",
                    str(path),
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Checkpoint
    # ------------------------------------------------------------------

    def checkpoint_check(self) -> DiagnosticCheck:
        path = self.runtime / "checkpoint_runtime.py"

        if not path.is_file():
            return self._blocked(
                "CHECKPOINT",
                "Checkpoint runtime unavailable",
                "Restore runtime/checkpoint_runtime.py",
            )

        return self._pass(
            "CHECKPOINT",
            "Checkpoint runtime surface available",
            (
                DiagnosticEvidence(
                    "runtime",
                    str(path),
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def recovery_check(self) -> DiagnosticCheck:
        handoff = self.runtime / "handoff_runtime.py"

        if handoff.is_file() or self.acrl.is_dir():
            return self._pass(
                "RECOVERY",
                "Recovery/continuity surface available",
                (
                    DiagnosticEvidence(
                        "recovery",
                        "ACRL/runtime handoff surface",
                    ),
                ),
            )

        return self._blocked(
            "RECOVERY",
            "Recovery surface unavailable",
            "Restore ACRL recovery or runtime handoff",
        )

    # ------------------------------------------------------------------
    # Integration
    # ------------------------------------------------------------------

    def integration_check(
        self,
        state: dict[str, Any] | None,
    ) -> DiagnosticCheck:
        if state is None:
            return self._blocked(
                "INTEGRATION",
                "Canonical state unavailable",
                "Repair STATE first",
            )

        if not self.acrl.is_dir():
            return self._blocked(
                "INTEGRATION",
                "ACRL unavailable",
                "Repair ACRL first",
            )

        if not self.runtime.is_dir():
            return self._blocked(
                "INTEGRATION",
                "Runtime unavailable",
                "Repair RUNTIME first",
            )

        return self._pass(
            "INTEGRATION",
            "Primary authority surfaces coexist",
            (
                DiagnosticEvidence(
                    "integration",
                    "CONTROL_CENTER + ACRL + RUNTIME",
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Position
    # ------------------------------------------------------------------

    @staticmethod
    def position_from_state(
        state: dict[str, Any] | None,
    ) -> DiagnosticPosition:
        if not state:
            return DiagnosticPosition()

        def find(*keys: str) -> str | None:
            for key in keys:
                if key in state:
                    value = state[key]

                    if isinstance(
                        value,
                        (str, int, float),
                    ):
                        return str(value)

            for container_key in (
                "execution_state",
                "current_state",
                "controller",
                "execution",
            ):
                container = state.get(container_key)

                if isinstance(container, dict):
                    for key in keys:
                        value = container.get(key)

                        if isinstance(
                            value,
                            (str, int, float),
                        ):
                            return str(value)

            return None

        return DiagnosticPosition(
            gate=find("current_gate", "gate"),
            task=find("current_task", "task"),
            subtask=find(
                "current_subtask",
                "subtask",
            ),
        )

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pass(
        key: str,
        summary: str,
        evidence: tuple[DiagnosticEvidence, ...] = (),
    ) -> DiagnosticCheck:
        return DiagnosticCheck(
            key=key,
            status=STATUS_PASS,
            summary=summary,
            evidence=evidence,
        )

    @staticmethod
    def _blocked(
        key: str,
        cause: str,
        next_action: str,
    ) -> DiagnosticCheck:
        return DiagnosticCheck(
            key=key,
            status=STATUS_BLOCKED,
            cause=cause,
            next_action=next_action,
        )
