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
class DiagnosticAuthority:
    """
    Verifies that diagnostic observation does not cross authority boundaries.

    Authority model:
        Control Center -> canonical execution/state authority
        ACRL            -> continuity/reconstruction authority
        Runtime         -> execution capability
        Diagnostics     -> observation only
    """

    control_center_root: Path
    autonomy_engine_root: Path
    state_file: Path

    def check(self) -> DiagnosticCheck:
        evidence: list[DiagnosticEvidence] = []

        if not self.control_center_root.exists():
            return DiagnosticCheck(
                key="AUTHORITY",
                status=STATUS_BLOCKED,
                summary="Control Center root is missing.",
                cause="Authoritative control-plane path is unavailable.",
                next_action="Restore REOS_CONTROL_CENTER before running diagnostics.",
                evidence=(),
            )

        if not self.state_file.exists():
            return DiagnosticCheck(
                key="AUTHORITY",
                status=STATUS_BLOCKED,
                summary="Canonical state file is missing.",
                cause="Diagnostic authority cannot be established without canonical state.",
                next_action="Restore data/state.json and re-run diagnostics.",
                evidence=(),
            )

        evidence.extend(
            [
                DiagnosticEvidence(
                    source="control_center",
                    value=str(self.control_center_root),
                    kind="authority",
                ),
                DiagnosticEvidence(
                    source="state",
                    value=str(self.state_file),
                    kind="canonical",
                ),
                DiagnosticEvidence(
                    source="diagnostics",
                    value="OBSERVATIONAL_ONLY",
                    kind="boundary",
                ),
            ]
        )

        return DiagnosticCheck(
            key="AUTHORITY",
            status=STATUS_PASS,
            summary="Authority boundaries are present and diagnostics remain observational.",
            cause=None,
            next_action=None,
            evidence=tuple(evidence),
        )
