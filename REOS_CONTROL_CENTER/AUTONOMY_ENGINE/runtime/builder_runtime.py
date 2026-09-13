from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime_orchestrator import RuntimeOrchestrator


class BuilderRuntime:
    """
    HOMIO Builder mode.

    Finds the authoritative current task and prepares the minimum
    evidence-driven engineering context required to work on it.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.orchestrator = RuntimeOrchestrator(
            self.root
        )

    def prepare_next_work(
        self,
    ) -> dict[str, Any]:
        return self.orchestrator.prepare(
            mode="HOMIO_BUILDER"
        ).to_dict()
