from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .diagnostic_models import (
    DiagnosticCheck,
    DiagnosticEvidence,
    STATUS_BLOCKED,
    STATUS_PASS,
)


@dataclass(frozen=True)
class DiagnosticDrift:
    """
    Minimal drift observer.

    This does not replace ACRL T10.
    It only detects obvious structural drift that would make
    a health result unsafe to trust.
    """

    control_center_root: Path
    state_file: Path
    autonomy_engine_root: Path

    def check(self) -> DiagnosticCheck:
        if not self.state_file.exists():
            return DiagnosticCheck(
                key="DRIFT",
                status=STATUS_BLOCKED,
                summary="Canonical state is unavailable for drift comparison.",
                cause="state.json does not exist.",
                next_action="Restore canonical state before evaluating drift.",
                evidence=(),
            )

        try:
            state = self._load_state()
        except (OSError, json.JSONDecodeError) as exc:
            return DiagnosticCheck(
                key="DRIFT",
                status=STATUS_BLOCKED,
                summary="Canonical state cannot be parsed.",
                cause=f"{type(exc).__name__}: {exc}",
                next_action="Repair or restore state.json before continuing.",
                evidence=(),
            )

        expected_engine = self.autonomy_engine_root.exists()

        evidence = [
            DiagnosticEvidence(
                source="state",
                value="PARSEABLE",
                kind="drift-baseline",
            ),
            DiagnosticEvidence(
                source="autonomy_engine",
                value="PRESENT" if expected_engine else "MISSING",
                kind="drift-baseline",
            ),
        ]

        suspicious = self._find_obvious_drift(state)

        if suspicious:
            return DiagnosticCheck(
                key="DRIFT",
                status=STATUS_BLOCKED,
                summary="Obvious canonical-state drift indicators detected.",
                cause="; ".join(suspicious),
                next_action="Run the existing ACRL drift analysis before making changes.",
                evidence=tuple(evidence),
            )

        return DiagnosticCheck(
            key="DRIFT",
            status=STATUS_PASS,
            summary="No obvious structural drift indicators detected.",
            cause=None,
            next_action=None,
            evidence=tuple(evidence),
        )

    def _load_state(self) -> dict[str, Any]:
        with self.state_file.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError("state.json root must be an object.")

        return data

    @staticmethod
    def _find_obvious_drift(state: dict[str, Any]) -> list[str]:
        findings: list[str] = []

      )

        if not state:
            findings.append("state.json is empty")

        return findings
