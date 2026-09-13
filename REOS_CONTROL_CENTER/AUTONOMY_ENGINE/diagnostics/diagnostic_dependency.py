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
class DiagnosticDependency:
    """
    Lightweight dependency-readiness adapter.

    This module does not replace ACRL T17/T27.
    It verifies the minimum repository relationships required
    for the health layer to reason safely.
    """

    control_center_root: Path
    autonomy_engine_root: Path
    acrl_root: Path
    runtime_root: Path

    def check(self) -> DiagnosticCheck:
        required_paths = {
            "control_center": self.control_center_root,
            "autonomy_engine": self.autonomy_engine_root,
            "acrl": self.acrl_root,
            "runtime": self.runtime_root,
        }

        missing = [
            name
            for name, path in required_paths.items()
            if not path.exists()
        ]

        if missing:
            return DiagnosticCheck(
                key="DEPENDENCY",
                status=STATUS_BLOCKED,
                summary="Required subsystem dependency is missing.",
                cause=f"Missing dependency: {', '.join(missing)}.",
                next_action="Restore the missing subsystem path and re-run diagnostics.",
                evidence=tuple(
                    DiagnosticEvidence(
                        source=name,
                        value=str(path),
                        kind="dependency",
                    )
                    for name, path in required_paths.items()
                ),
            )

        evidence = tuple(
            DiagnosticEvidence(
                source=name,
                value=str(path),
                kind="dependency",
            )
            for name, path in required_paths.items()
        )

        return DiagnosticCheck(
            key="DEPENDENCY",
            status=STATUS_PASS,
            summary="Core subsystem dependency graph is structurally available.",
            cause=None,
            next_action=None,
            evidence=evidence,
        )
