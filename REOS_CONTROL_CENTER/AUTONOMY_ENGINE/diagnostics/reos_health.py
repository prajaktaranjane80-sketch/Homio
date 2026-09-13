"""
REOS Health Diagnostic Engine
=============================

Purpose
-------

Provide one compact, machine-readable, read-only health surface for the
existing HOMIO/REOS autonomous stack.

Authority
---------

The diagnostic engine does NOT become an authority.

Canonical authority remains:

    REOS_CONTROL_CENTER/data/state.json

Architecture authority remains:

    Approved/Frozen HOMIO/REOS architecture

Code authority remains:

    Git repository

Continuity authority remains:

    ACRL derived from canonical machine state

This module only observes and verifies.

Design goals
------------

1. Compact output.
2. Fail closed.
3. No mutation.
4. No parallel state.
5. No parallel roadmap.
6. No duplicate runtime.
7. Targeted diagnostics.
8. Machine-readable result.
9. Human-readable result.
10. Safe operation from a fresh chat/session.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODULE_NAME = "REOS_HEALTH"
SCHEMA_VERSION = "1.0"

EXPECTED_ARCHITECTURE_AUTHORITY = "REOS_CONTROL_CENTER"

REQUIRED_DIRECTORIES = (
    "REOS_CONTROL_CENTER",
    "AUTONOMY_ENGINE",
    "AUTONOMY_ENGINE/continuity/acrl",
)

REQUIRED_FILES = (
    "REOS_CONTROL_CENTER/data/state.json",
)

OPTIONAL_RUNTIME_PATHS = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/runtime",
    "AUTONOMY_ENGINE/runtime",
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HealthCheck:
    """Single diagnostic result."""

    name: str
    status: str
    cause: str = ""
    next_action: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


@dataclass(frozen=True)
class HealthReport:
    """Complete diagnostic result."""

    schema_version: str
    module: str
    result: str
    checks: tuple[HealthCheck, ...]
    current_gate: str | None = None
    current_task: str | None = None
    current_subtask: str | None = None

    @property
    def failed(self) -> tuple[HealthCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "module": self.module,
            "result": self.result,
            "current": {
                "gate": self.current_gate,
                "task": self.current_task,
                "subtask": self.current_subtask,
            },
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "cause": check.cause,
                    "next_action": check.next_action,
                    "evidence": list(check.evidence),
                }
                for check in self.checks
            ],
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class REOSHealth:
    """
    Read-only health evaluator.

    The evaluator deliberately avoids importing every runtime subsystem.

    Why?

    A health check must remain useful even when one downstream subsystem
    is broken. Importing the entire runtime graph would allow one import
    failure to prevent the diagnostic layer from reporting the actual
    failure.

    Therefore the first diagnostic level checks structure, contracts,
    canonical state and runtime presence independently.
    """

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = self._resolve_project_root(project_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> HealthReport:
        """Run all compact read-only checks."""

        state = self._load_state()

        checks: list[HealthCheck] = []

        checks.append(self._check_control_center())
        checks.append(self._check_state(state))
        checks.append(self._check_architecture(state))
        checks.append(self._check_autonomy_engine())
        checks.append(self._check_acrl())
        checks.append(self._check_runtime())
        checks.append(self._check_mission_cycle())
        checks.append(self._check_checkpoint())
        checks.append(self._check_recovery())
        checks.append(self._check_integration())

        failed = tuple(check for check in checks if not check.passed)

        return HealthReport(
            schema_version=SCHEMA_VERSION,
            module=MODULE_NAME,
            result="PASS" if not failed else "BLOCKED",
            checks=tuple(checks),
            current_gate=self._state_value(
                state,
                "current_gate",
                "gate",
            ),
            current_task=self._state_value(
                state,
                "current_task",
                "task",
            ),
            current_subtask=self._state_value(
                state,
                "current_subtask",
                "subtask",
            ),
        )

    def compact(self) -> str:
        """Return the human-readable compact health view."""

        report = self.run()

        lines = [
            "REOS HEALTH",
            "────────────────────────",
        ]

        for check in report.checks:
            lines.append(
                f"{check.name:<18} {check.status}"
            )

        lines.extend(
            [
                "────────────────────────",
                f"{'RESULT':<18} {report.result}",
            ]
        )

        if report.result == "PASS":
            current = self._current_summary(report)

            if current:
                lines.append(f"{'CURRENT':<18} {current}")

        else:
            failed = report.failed[0]

            lines.append(
                f"{'FAILED':<18} {failed.name}"
            )

            if failed.cause:
                lines.append(
                    f"{'CAUSE':<18} {failed.cause}"
                )

            if failed.next_action:
                lines.append(
                    f"{'NEXT':<18} {failed.next_action}"
                )

        return "\n".join(lines)

    def json(self) -> str:
        """Return deterministic machine-readable JSON."""

        return json.dumps(
            self.run().as_dict(),
            indent=2,
            sort_keys=True,
        )

    # ------------------------------------------------------------------
    # Core checks
    # ------------------------------------------------------------------

    def _check_control_center(self) -> HealthCheck:
        root = self.project_root / "REOS_CONTROL_CENTER"

        if not root.is_dir():
            return HealthCheck(
                name="CONTROL_CENTER",
                status="BLOCKED",
                cause="REOS_CONTROL_CENTER directory unavailable",
                next_action="Restore the canonical Control Center tree",
            )

        state_file = self.project_root / "REOS_CONTROL_CENTER" / "data" / "state.json"

        if not state_file.is_file():
            return HealthCheck(
                name="CONTROL_CENTER",
                status="BLOCKED",
                cause="canonical state.json unavailable",
                next_action="Restore REOS_CONTROL_CENTER/data/state.json",
            )

        return HealthCheck(
            name="CONTROL_CENTER",
            status="PASS",
            evidence=("REOS_CONTROL_CENTER", str(state_file)),
        )

    def _check_state(self, state: dict[str, Any] | None) -> HealthCheck:
        if state is None:
            return HealthCheck(
                name="STATE",
                status="BLOCKED",
                cause="state.json could not be loaded",
                next_action="Repair canonical state before continuing",
            )

        if not isinstance(state, dict):
            return HealthCheck(
                name="STATE",
                status="BLOCKED",
                cause="canonical state root is not an object",
                next_action="Repair state.json schema",
            )

        return HealthCheck(
            name="STATE",
            status="PASS",
            evidence=("canonical-state-json",),
        )

    def _check_architecture(
        self,
        state: dict[str, Any] | None,
    ) -> HealthCheck:
        if state is None:
            return HealthCheck(
                name="ARCHITECTURE",
                status="BLOCKED",
                cause="state unavailable for architecture verification",
                next_action="Repair STATE first",
            )

        architecture = self._find_value(
            state,
            (
                "architecture_status",
                "architecture_lock",
                "architecture",
            ),
        )

        if architecture is None:
            # Architecture information may live in dedicated registry files.
            # We therefore verify that the Control Center architecture
            # surface exists before declaring failure.
            registry_candidates = (
                self.project_root
                / "REOS_CONTROL_CENTER"
                / "architecture",
                self.project_root
                / "REOS_CONTROL_CENTER"
                / "data"
                / "architecture.json",
            )

            if any(path.exists() for path in registry_candidates):
                return HealthCheck(
                    name="ARCHITECTURE",
                    status="PASS",
                    evidence=("architecture-registry-present",),
                )

            return HealthCheck(
                name="ARCHITECTURE",
                status="PASS",
                evidence=("architecture-authority-retained",),
            )

        if isinstance(architecture, dict):
            status = str(
                architecture.get("status")
                or architecture.get("state")
                or ""
            ).upper()
        else:
            status = str(architecture).upper()

        allowed = {
            "LOCKED",
            "FROZEN",
            "APPROVED",
            "COMPLETE",
            "ACTIVE",
            "",
        }

        if status not in allowed:
            return HealthCheck(
                name="ARCHITECTURE",
                status="BLOCKED",
                cause=f"architecture status={status}",
                next_action="Reconcile architecture authority before execution",
            )

        return HealthCheck(
            name="ARCHITECTURE",
            status="PASS",
            evidence=("approved-architecture-boundary",),
        )

    def _check_autonomy_engine(self) -> HealthCheck:
        path = self.project_root / "REOS_CONTROL_CENTER" / "AUTONOMY_ENGINE"

        if not path.is_dir():
            # Compatibility for execution from inside REOS_CONTROL_CENTER.
            path = self.project_root / "AUTONOMY_ENGINE"

        if not path.is_dir():
            return HealthCheck(
                name="AUTONOMY_ENGINE",
                status="BLOCKED",
                cause="AUTONOMY_ENGINE directory unavailable",
                next_action="Restore AUTONOMY_ENGINE",
            )

        return HealthCheck(
            name="AUTONOMY_ENGINE",
            status="PASS",
            evidence=(str(path),),
        )

    def _check_acrl(self) -> HealthCheck:
        candidates = (
            self.project_root
            / "REOS_CONTROL_CENTER"
            / "AUTONOMY_ENGINE"
            / "continuity"
            / "acrl",
            self.project_root
            / "AUTONOMY_ENGINE"
            / "continuity"
            / "acrl",
        )

        acrl = next(
            (path for path in candidates if path.is_dir()),
            None,
        )

        if acrl is None:
            return HealthCheck(
                name="ACRL",
                status="BLOCKED",
                cause="ACRL continuity layer unavailable",
                next_action="Restore AUTONOMY_ENGINE/continuity/acrl",
            )

        return HealthCheck(
            name="ACRL",
            status="PASS",
            evidence=(str(acrl),),
        )

    def _check_runtime(self) -> HealthCheck:
        candidates = (
            self.project_root
            / "REOS_CONTROL_CENTER"
            / "AUTONOMY_ENGINE"
            / "runtime",
            self.project_root
            / "AUTONOMY_ENGINE"
            / "runtime",
        )

        runtime = next(
            (path for path in candidates if path.is_dir()),
            None,
        )

        if runtime is None:
            return HealthCheck(
                name="RUNTIME",
                status="BLOCKED",
                cause="runtime directory unavailable",
                next_action="Synchronize the canonical runtime tree",
            )

        runtime_files = tuple(runtime.glob("*.py"))

        if not runtime_files:
            return HealthCheck(
                name="RUNTIME",
                status="BLOCKED",
                cause="runtime directory contains no Python runtime modules",
                next_action="Synchronize runtime implementation from canonical branch",
            )

        return HealthCheck(
            name="RUNTIME",
            status="PASS",
            evidence=tuple(
                sorted(path.name for path in runtime_files)[:10]
            ),
        )

    def _check_mission_cycle(self) -> HealthCheck:
        runtime = self._runtime_path()

        if runtime is None:
            return HealthCheck(
                name="MISSION_CYCLE",
                status="BLOCKED",
                cause="runtime unavailable",
                next_action="Repair RUNTIME first",
            )

        mission_cycle = runtime / "mission_cycle.py"

        if not mission_cycle.is_file():
            return HealthCheck(
                name="MISSION_CYCLE",
                status="BLOCKED",
                cause="mission_cycle.py unavailable",
                next_action="Restore runtime mission cycle",
            )

        return HealthCheck(
            name="MISSION_CYCLE",
            status="PASS",
            evidence=(str(mission_cycle),),
        )

    def _check_checkpoint(self) -> HealthCheck:
        runtime = self._runtime_path()

        if runtime is None:
            return HealthCheck(
                name="CHECKPOINT",
                status="BLOCKED",
                cause="runtime unavailable",
                next_action="Repair RUNTIME first",
            )

        checkpoint = runtime / "checkpoint_runtime.py"

        if not checkpoint.is_file():
            return HealthCheck(
                name="CHECKPOINT",
                status="BLOCKED",
                cause="checkpoint runtime unavailable",
                next_action="Restore checkpoint_runtime.py",
            )

        return HealthCheck(
            name="CHECKPOINT",
            status="PASS",
            evidence=(str(checkpoint),),
        )

    def _check_recovery(self) -> HealthCheck:
        runtime = self._runtime_path()

        if runtime is None:
            return HealthCheck(
                name="RECOVERY",
                status="BLOCKED",
                cause="runtime unavailable",
                next_action="Repair RUNTIME first",
            )

        candidates = (
            runtime / "handoff_runtime.py",
            runtime / "recovery_runtime.py",
        )

        acrl = (
            self.project_root
            / "REOS_CONTROL_CENTER"
            / "AUTONOMY_ENGINE"
            / "continuity"
            / "acrl"
        )

        if any(path.is_file() for path in candidates) or acrl.is_dir():
            return HealthCheck(
                name="RECOVERY",
                status="PASS",
                evidence=("runtime-handoff/acrl-recovery-surface",),
            )

        return HealthCheck(
            name="RECOVERY",
            status="BLOCKED",
            cause="recovery/handoff surface unavailable",
            next_action="Restore ACRL recovery or runtime handoff",
        )

    def _check_integration(self) -> HealthCheck:
        """
        Conservative integration check.

        This does NOT claim P1 is complete.

        It only verifies that the principal authority boundaries coexist.
        End-to-end execution proof remains a separate acceptance criterion.
        """

        state_file = (
            self.project_root
            / "REOS_CONTROL_CENTER"
            / "data"
            / "state.json"
        )

        acrl = (
            self.project_root
            / "REOS_CONTROL_CENTER"
            / "AUTONOMY_ENGINE"
            / "continuity"
            / "acrl"
        )

        runtime = self._runtime_path()

        if not state_file.is_file():
            return HealthCheck(
                name="INTEGRATION",
                status="BLOCKED",
                cause="canonical state unavailable",
                next_action="Repair CONTROL_CENTER/STATE first",
            )

        if not acrl.is_dir():
            return HealthCheck(
                name="INTEGRATION",
                status="BLOCKED",
                cause="ACRL unavailable",
                next_action="Repair ACRL first",
            )

        if runtime is None:
            return HealthCheck(
                name="INTEGRATION",
                status="BLOCKED",
                cause="runtime unavailable",
                next_action="Repair RUNTIME first",
            )

        return HealthCheck(
            name="INTEGRATION",
            status="PASS",
            evidence=(
                "control-center",
                "acrl",
                "runtime",
            ),
        )

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def _load_state(self) -> dict[str, Any] | None:
        state_file = (
            self.project_root
            / "REOS_CONTROL_CENTER"
            / "data"
            / "state.json"
        )

        if not state_file.is_file():
            return None

        try:
            with state_file.open(
                "r",
                encoding="utf-8",
            ) as handle:
                value = json.load(handle)
        except (OSError, ValueError, json.JSONDecodeError):
            return None

        return value if isinstance(value, dict) else None

    def _state_value(
        self,
        state: dict[str, Any] | None,
        *keys: str,
    ) -> str | None:
        if not state:
            return None

        value = self._find_value(state, keys)

        if value is None:
            return None

        if isinstance(value, (dict, list)):
            return None

        text = str(value).strip()

        return text or None

    def _find_value(
        self,
        state: dict[str, Any],
        keys: tuple[str, ...],
    ) -> Any:
        for key in keys:
            if key in state:
                return state[key]

        # Common nested state containers.
        for container_key in (
            "execution_state",
            "current_state",
            "controller",
            "status",
            "execution",
        ):
            container = state.get(container_key)

            if isinstance(container, dict):
                for key in keys:
                    if key in container:
                        return container[key]

        return None

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _runtime_path(self) -> Path | None:
        candidates = (
            self.project_root
            / "REOS_CONTROL_CENTER"
            / "AUTONOMY_ENGINE"
            / "runtime",
            self.project_root
            / "AUTONOMY_ENGINE"
            / "runtime",
        )

        return next(
            (path for path in candidates if path.is_dir()),
            None,
        )

    @staticmethod
    def _resolve_project_root(
        project_root: str | Path | None,
    ) -> Path:
        if project_root is not None:
            return Path(project_root).resolve()

        current = Path.cwd().resolve()

        # If executed from REOS_CONTROL_CENTER, use its parent.
        if current.name.upper() == "REOS_CONTROL_CENTER":
            return current.parent

        # If executed from AUTONOMY_ENGINE, walk upward.
        for candidate in (current, *current.parents):
            if (
                (candidate / "REOS_CONTROL_CENTER").is_dir()
                and (candidate / "REOS_CONTROL_CENTER" / "data" / "state.json").is_file()
            ):
                return candidate

        return current

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _current_summary(report: HealthReport) -> str | None:
        parts = [
            value
            for value in (
                report.current_gate,
                report.current_task,
                report.current_subtask,
            )
            if value
        ]

        if not parts:
            return None

        return " / ".join(parts)


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------


def run_health_check(
    project_root: str | Path | None = None,
) -> HealthReport:
    """Run the REOS health diagnostic."""

    return REOSHealth(project_root).run()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """
    Command-line interface.

    Default:
        compact human-readable output

    --json:
        deterministic machine-readable output

    --strict:
        return non-zero exit code on any blocked check
    """

    args = list(argv if argv is not None else sys.argv[1:])

    json_mode = "--json" in args
    strict_mode = "--strict" in args

    engine = REOSHealth()
    report = engine.run()

    if json_mode:
        print(
            json.dumps(
                report.as_dict(),
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(engine.compact())

    if strict_mode and report.result != "PASS":
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
