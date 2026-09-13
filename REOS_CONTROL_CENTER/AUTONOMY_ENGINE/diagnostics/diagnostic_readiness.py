from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .diagnostic_models import (
    DiagnosticCheck,
    DiagnosticEvidence,
    STATUS_BLOCKED,
    STATUS_PASS,
)


@dataclass(frozen=True)
class DiagnosticReadiness:
    """
    Determines whether the minimum execution/readiness surface exists.

    This does NOT claim that P1 is complete.
    It only verifies structural readiness signals.
    """

    control_center_root: Path
    autonomy_engine_root: Path
    runtime_root: Path

    def check(self) -> DiagnosticCheck:
        runtime_files = {
            "mission_cycle": self.runtime_root / "mission_cycle.py",
            "execution_runtime": self.runtime_root / "execution_runtime.py",
            "autonomous_mission_runtime": (
                self.runtime_root / "autonomous_mission_runtime.py"
            ),
        }

        missing = [
            name
            for name, path in runtime_files.items()
            if not path.exists()
        ]

        evidence = tuple(
            DiagnosticEvidence(
                source=name,
                value="PRESENT" if path.exists() else "MISSING",
                kind="readiness",
            )
            for name, path in runtime_files.items()
        )

        if missing:
            return DiagnosticCheck(
                key="READINESS",
                status=STATUS_BLOCKED,
                summary="Runtime readiness surface is incomplete.",
                cause=f"Missing runtime component(s): {', '.join(missing)}.",
                next_action="Restore the missing runtime component(s) before execution readiness can be trusted.",
                evidence=evidence,
            )

        return DiagnosticCheck(
            key="READINESS",
            status=STATUS_PASS,
            summary="Minimum runtime readiness surface is structurally available.",
            cause=None,
            next_action=None,
            evidence=evidence,
        )
