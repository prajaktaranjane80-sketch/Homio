from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .runtime_bindings import (
    RuntimeBinding,
    T21_TO_T30_BINDINGS,
    resolve_all_bindings,
)
from .unified_runtime_context import UnifiedRuntimeContext


@dataclass(frozen=True, slots=True)
class RuntimeIntegrationSnapshot:
    mission_id: str
    context_fingerprint: str
    registered_task_count: int
    bound_task_ids: tuple[str, ...]
    components: tuple[tuple[str, str], ...]
    healthy: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "mission_id": self.mission_id,
            "context_fingerprint": self.context_fingerprint,
            "registered_task_count": self.registered_task_count,
            "bound_task_ids": list(self.bound_task_ids),
            "components": [
                {
                    "task_id": task_id,
                    "component": component,
                }
                for task_id, component in self.components
            ],
            "healthy": self.healthy,
        }


class ACRLRuntimeOrchestrator:
    """
    INT-02 runtime binding/orchestration boundary.

    This layer:
    - consumes INT-01 UnifiedRuntimeContext
    - verifies T21–T30 runtime exports
    - binds existing ACRL components
    - produces deterministic integration evidence

    This layer does NOT:
    - mutate state.json
    - execute Git transactions
    - execute business operations
    - bypass T18/T20/T21/T22 controls
    - create T31+ ACRL tasks
    """

    def __init__(
        self,
        context: UnifiedRuntimeContext,
    ) -> None:
        self.context = context

    def build_snapshot(self) -> RuntimeIntegrationSnapshot:
        if len(self.context.acrl_task_ids) != 30:
            raise ValueError(
                "INT-02 requires the complete T01–T30 ACRL spine."
            )

        expected_ids = tuple(
            f"T{number:02d}"
            for number in range(1, 31)
        )

        if self.context.acrl_task_ids != expected_ids:
            raise ValueError(
                "INT-02 ACRL task order mismatch."
            )

        resolved = resolve_all_bindings()

        component_rows: list[tuple[str, str]] = []

        for binding in T21_TO_T30_BINDINGS:
            component = resolved[binding.task_id]

            component_name = getattr(
                component,
                "__name__",
                component.__class__.__name__,
            )

            component_rows.append(
                (
                    binding.task_id,
                    component_name,
                )
            )

        bound_ids = tuple(
            task_id
            for task_id, _ in component_rows
        )

        healthy = (
            bound_ids
            == tuple(
                f"T{number:02d}"
                for number in range(21, 31)
            )
            and len(resolved) == 10
        )

        return RuntimeIntegrationSnapshot(
            mission_id=self.context.mission_id,
            context_fingerprint=self.context.context_fingerprint,
            registered_task_count=len(
                self.context.acrl_task_ids
            ),
            bound_task_ids=bound_ids,
            components=tuple(component_rows),
            healthy=healthy,
        )

    def validate(self) -> bool:
        return self.build_snapshot().healthy
