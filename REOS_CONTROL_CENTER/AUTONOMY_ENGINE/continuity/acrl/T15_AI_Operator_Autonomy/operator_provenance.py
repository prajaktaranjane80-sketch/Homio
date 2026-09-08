"""
ACRL T15 — Operator Provenance.

Tracks why a T15 proposal exists and what evidence supports it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OperatorProvenance:
    """Immutable provenance record."""

    provenance_version: str
    authority: str
    source: str
    gate: str
    subtask: str | None
    task: str
    evidence: tuple[str, ...]
    request_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_version": self.provenance_version,
            "authority": self.authority,
            "source": self.source,
            "gate": self.gate,
            "subtask": self.subtask,
            "task": self.task,
            "evidence": list(self.evidence),
            "request_fingerprint": self.request_fingerprint,
        }


class OperatorProvenanceEngine:
    """T15 provenance construction and validation."""

    PROVENANCE_VERSION = "T15-PROVENANCE-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def build(
        cls,
        *,
        source: str,
        gate: str,
        subtask: str | None,
        task: str,
        evidence: tuple[str, ...],
        request_fingerprint: str,
    ) -> OperatorProvenance:
        if not isinstance(source, str) or not source.strip():
            raise ValueError(
                "Provenance source must be non-empty."
            )

        if not isinstance(gate, str) or not gate.strip():
            raise ValueError(
                "Provenance gate must be non-empty."
            )

        if not isinstance(task, str) or not task.strip():
            raise ValueError(
                "Provenance task must be non-empty."
            )

        if not isinstance(evidence, tuple):
            raise ValueError(
                "Provenance evidence must be a tuple."
            )

        if (
            not isinstance(request_fingerprint, str)
            or len(request_fingerprint) != 64
        ):
            raise ValueError(
                "Invalid provenance request fingerprint."
            )

        return OperatorProvenance(
            provenance_version=cls.PROVENANCE_VERSION,
            authority=cls.AUTHORITY,
            source=source,
            gate=gate,
            subtask=subtask,
            task=task,
            evidence=evidence,
            request_fingerprint=request_fingerprint,
        )

    @classmethod
    def validate(
        cls,
        provenance: OperatorProvenance,
    ) -> bool:
        if not isinstance(
            provenance,
            OperatorProvenance,
        ):
            raise TypeError(
                "provenance must be an OperatorProvenance."
            )

        if (
            provenance.provenance_version
            != cls.PROVENANCE_VERSION
        ):
            raise ValueError(
                "Unsupported T15 provenance version."
            )

        if provenance.authority != cls.AUTHORITY:
            raise ValueError(
                "Invalid T15 provenance authority."
            )

        if not provenance.source.strip():
            raise ValueError(
                "Provenance source cannot be empty."
            )

        if not provenance.gate.strip():
            raise ValueError(
                "Provenance gate cannot be empty."
            )

        if not provenance.task.strip():
            raise ValueError(
                "Provenance task cannot be empty."
            )

        if (
            not isinstance(
                provenance.request_fingerprint,
                str,
            )
            or len(provenance.request_fingerprint) != 64
        ):
            raise ValueError(
                "Invalid provenance request fingerprint."
            )

        return True


__all__ = [
    "OperatorProvenance",
    "OperatorProvenanceEngine",
]
