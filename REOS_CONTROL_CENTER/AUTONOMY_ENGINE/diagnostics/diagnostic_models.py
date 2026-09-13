"""
REOS Diagnostic Models
======================

Immutable data contracts used by the diagnostic subsystem.

This module contains no filesystem mutation and no execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


STATUS_PASS = "PASS"
STATUS_BLOCKED = "BLOCKED"
STATUS_SKIPPED = "SKIPPED"

RESULT_PASS = "PASS"
RESULT_BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class DiagnosticEvidence:
    """
    Small machine-readable evidence item.

    Evidence is descriptive only. It does not become canonical project state.
    """

    source: str
    value: str
    kind: str = "observation"


@dataclass(frozen=True)
class DiagnosticCheck:
    """
    Result of one isolated diagnostic probe.
    """

    key: str
    status: str
    summary: str = ""
    cause: str = ""
    next_action: str = ""
    evidence: tuple[DiagnosticEvidence, ...] = field(
        default_factory=tuple
    )

    @property
    def passed(self) -> bool:
        return self.status == STATUS_PASS

    @property
    def blocked(self) -> bool:
        return self.status == STATUS_BLOCKED


@dataclass(frozen=True)
class DiagnosticPosition:
    """
    Current project position reconstructed from canonical state.
    """

    gate: str | None = None
    task: str | None = None
    subtask: str | None = None

    def compact(self) -> str | None:
        parts = tuple(
            value
            for value in (
                self.gate,
                self.task,
                self.subtask,
            )
            if value
        )

        if not parts:
            return None

        return " / ".join(parts)


@dataclass(frozen=True)
class DiagnosticReport:
    """
    Complete read-only health report.
    """

    schema_version: str
    result: str
    checks: tuple[DiagnosticCheck, ...]
    position: DiagnosticPosition = field(
        default_factory=DiagnosticPosition
    )
    fingerprint: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def passed(self) -> bool:
        return self.result == RESULT_PASS

    @property
    def blocked(self) -> bool:
        return self.result == RESULT_BLOCKED

    @property
    def failed_checks(self) -> tuple[DiagnosticCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if check.status == STATUS_BLOCKED
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "result": self.result,
            "position": {
                "gate": self.position.gate,
                "task": self.position.task,
                "subtask": self.position.subtask,
            },
            "fingerprint": self.fingerprint,
            "checks": [
                {
                    "key": check.key,
                    "status": check.status,
                    "summary": check.summary,
                    "cause": check.cause,
                    "next_action": check.next_action,
                    "evidence": [
                        {
                            "source": item.source,
                            "value": item.value,
                            "kind": item.kind,
                        }
                        for item in check.evidence
                    ],
                }
                for check in self.checks
            ],
            "metadata": dict(self.metadata),
        }
