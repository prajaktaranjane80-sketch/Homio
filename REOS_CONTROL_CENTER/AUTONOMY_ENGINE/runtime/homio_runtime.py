from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime_orchestrator import RuntimeOrchestrator


class HOMIORuntime:
    """
    HOMIO production-oriented autonomous runtime shell.

    Initial runtime remains observe/verify/govern-first.
    It does not invent production mutations.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.orchestrator = RuntimeOrchestrator(
            self.root
        )

    def observe(self) -> dict[str, Any]:
        return self.orchestrator.prepare(
            mode="HOMIO_RUNTIME"
        ).to_dict()

    def health_contract(self) -> dict[str, Any]:
        return {
            "mode": "HOMIO_RUNTIME",
            "observe": True,
            "verify": True,
            "govern": True,
            "execute": False,
            "recover": True,
            "escalate": True,
            "direct_state_mutation": False,
            "direct_repository_mutation": False,
            "controller_authority": (
                "REOS_CONTROL_CENTER"
            ),
            "mutation_boundary": (
                "ControllerExecutor/ExecutionPipeline"
            ),
        }
