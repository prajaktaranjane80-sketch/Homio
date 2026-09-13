"""
REOS Diagnostic Registry
========================

Central registry of diagnostic layers.

The registry is not a roadmap and not a runtime scheduler.

It only describes which read-only diagnostic probes exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .diagnostic_models import DiagnosticCheck


Probe = Callable[[], DiagnosticCheck]


@dataclass(frozen=True)
class DiagnosticDefinition:
    """
    Definition of one diagnostic probe.
    """

    key: str
    description: str
    critical: bool
    probe: Probe


class DiagnosticRegistry:
    """
    Deterministic registry.

    Registration order is preserved deliberately so compact output remains
    stable across sessions.
    """

    def __init__(self) -> None:
        self._definitions: list[DiagnosticDefinition] = []

    def register(
        self,
        definition: DiagnosticDefinition,
    ) -> None:
        if any(
            item.key == definition.key
            for item in self._definitions
        ):
            raise ValueError(
                f"Duplicate diagnostic key: {definition.key}"
            )

        self._definitions.append(definition)

    def definitions(
        self,
    ) -> tuple[DiagnosticDefinition, ...]:
        return tuple(self._definitions)

    def keys(self) -> tuple[str, ...]:
        return tuple(
            definition.key
            for definition in self._definitions
        )

    def run_all(self) -> tuple[DiagnosticCheck, ...]:
        """
        Run probes independently.

        A broken probe must become BLOCKED rather than crash the complete
        diagnostic surface.
        """

        results: list[DiagnosticCheck] = []

        for definition in self._definitions:
            try:
                result = definition.probe()
            except Exception as exc:
                result = DiagnosticCheck(
                    key=definition.key,
                    status="BLOCKED",
                    summary="Diagnostic probe failed",
                    cause=f"{type(exc).__name__}: {exc}",
                    next_action=(
                        f"Inspect diagnostic probe: {definition.key}"
                    ),
                )

            results.append(result)

        return tuple(results)
