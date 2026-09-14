"""ACRL T05 — Task Dependency Reconstruction.

Read-only reconstruction of the dependency context required to determine
the next valid authoritative work unit.

Authoritative source:
    REOS_CONTROL_CENTER/data/state.json

This module consumes:
    - T03 execution-state reconstruction
    - canonical gate_plans
    - canonical dependency nodes/edges/rules

It does NOT:
    - modify state.json
    - create dependency state
    - invent module dependencies
    - advance gates
    - complete subtasks
    - authorize execution
    - replace REOS_CONTROL_CENTER
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from AUTONOMY_ENGINE.continuity.acrl.T03_State_Reconstruction.state_reconstruction import (
    ExecutionStateReconstructor,
    StateReconstructionError,
)


class TaskDependencyError(RuntimeError):
    """Base T05 task-dependency failure."""


class TaskDependencySourceError(TaskDependencyError):
    """Authoritative dependency state cannot be loaded."""


class TaskDependencyIntegrityError(TaskDependencyError):
    """Dependency graph is structurally invalid."""


class TaskDependencyConflictError(TaskDependencyError):
    """Dependency relationships contain a conflict."""


class DependencyResolutionStatus(str, Enum):
    VALID = "VALID"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class DependencyBlocker:
    """Immutable description of one dependency blocker."""

    kind: str
    dependency_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "dependency_id": self.dependency_id,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class TaskDependencyResolution:
    """Complete immutable dependency reconstruction."""

    current_gate: str
    current_task: str
    current_subtask: str
    current_subtask_status: str

    prerequisite_gates: tuple[str, ...]
    prerequisite_subtasks: tuple[str, ...]
    prerequisite_modules: tuple[str, ...]

    dependency_owners: tuple[tuple[str, str], ...]

    blocked_by: tuple[DependencyBlocker, ...]
    conflicts: tuple[str, ...]

    first_valid_work_unit: str
    status: DependencyResolutionStatus

    dependency_fingerprint: str
    source_state_sha256: str

    def can_resume(self) -> bool:
        return self.status is DependencyResolutionStatus.VALID

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "current": {
                "gate": self.current_gate,
                "task": self.current_task,
                "subtask": self.current_subtask,
                "subtask_status": self.current_subtask_status,
            },
            "dependencies": {
                "prerequisite_gates": list(self.prerequisite_gates),
                "prerequisite_subtasks": list(
                    self.prerequisite_subtasks
                ),
                "prerequisite_modules": list(
                    self.prerequisite_modules
                ),
                "dependency_owners": {
                    key: value
                    for key, value in self.dependency_owners
                },
            },
            "blocked_by": [
                item.to_dict()
                for item in self.blocked_by
            ],
            "conflicts": list(self.conflicts),
            "resolution": {
                "first_valid_work_unit": self.first_valid_work_unit,
                "status": self.status.value,
            },
            "authority": {
                "canonical_source": "data/state.json",
                "source_state_sha256": self.source_state_sha256,
            },
            "fingerprint": self.dependency_fingerprint,
        }


class TaskDependencyReconstructor:
    """Reconstruct the authoritative dependency context."""

    COMPLETE_GATE_STATUSES = {
        "APPROVED",
        "COMPLETE",
        "COMPLETED",
        "DONE",
        "FROZEN",
    }

    COMPLETE_SUBTASK_STATUS = "DONE"

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            self.root = Path(__file__).resolve().parents[4]
        else:
            self.root = Path(control_center_root)

        self.state_path = self.root / "data" / "state.json"

    @staticmethod
    def _read_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise TaskDependencySourceError(
                f"Authoritative state not found: {path}"
            )

        if not path.is_file():
            raise TaskDependencySourceError(
                f"Authoritative state is not a file: {path}"
            )

        try:
            raw = path.read_text(encoding="utf-8-sig")
            state = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise TaskDependencySourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(state, dict):
            raise TaskDependencySourceError(
                "Authoritative state must be a JSON object."
            )

        return state

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise TaskDependencyIntegrityError(
                f"{field_name} must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _string_list(
        value: Any,
        field_name: str,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise TaskDependencyIntegrityError(
                f"{field_name} must be a list."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise TaskDependencyIntegrityError(
                    f"{field_name} contains an invalid entry."
                )

            result.append(item.strip())

        return tuple(result)

    @staticmethod
    def _state_sha256(path: Path) -> str:
        try:
            return hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        except OSError as exc:
            raise TaskDependencySourceError(
                f"Unable to fingerprint authoritative state: {path}"
            ) from exc

    @classmethod
    def _is_gate_complete(
        cls,
        gate: Mapping[str, Any],
    ) -> bool:
        status = gate.get("status")

        if (
            isinstance(status, str)
            and status.strip().upper()
            in cls.COMPLETE_GATE_STATUSES
        ):
            subtasks = gate.get("subtasks")

            if isinstance(subtasks, list) and subtasks:
                return all(
                    isinstance(item, Mapping)
                    and isinstance(item.get("status"), str)
                    and item["status"].strip().upper()
                    == cls.COMPLETE_SUBTASK_STATUS
                    for item in subtasks
                )

            return True

        return False

    @staticmethod
    def _build_predecessor_graph(
        edges: Any,
    ) -> dict[str, tuple[str, ...]]:
        if not isinstance(edges, list):
            raise TaskDependencyIntegrityError(
                "dependencies.edges must be a list."
            )

        predecessors: dict[str, list[str]] = {}

        for edge in edges:
            if (
                not isinstance(edge, list)
                or len(edge) != 2
            ):
                raise TaskDependencyIntegrityError(
                    "Each dependency edge must be [source, target]."
                )

            source, target = edge

            if (
                not isinstance(source, str)
                or not source.strip()
                or not isinstance(target, str)
                or not target.strip()
            ):
                raise TaskDependencyIntegrityError(
                    "Dependency edge contains invalid node ID."
                )

            source = source.strip()
            target = target.strip()

            predecessors.setdefault(target, [])

            if source not in predecessors[target]:
                predecessors[target].append(source)

        return {
            key: tuple(value)
            for key, value in predecessors.items()
        }

    @staticmethod
    def _transitive_predecessors(
        current_gate: str,
        predecessors: Mapping[str, tuple[str, ...]],
    ) -> tuple[str, ...]:
        result: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def walk(node: str) -> None:
            if node in visiting:
                raise TaskDependencyConflictError(
                    "Dependency graph contains a cycle."
                )

            if node in visited:
                return

            visiting.add(node)

            for parent in predecessors.get(node, ()):
                walk(parent)

                if parent not in result:
                    result.append(parent)

            visiting.remove(node)
            visited.add(node)

        walk(current_gate)

        return tuple(result)

    @staticmethod
    def _optional_modules(
        gate: Mapping[str, Any],
    ) -> tuple[str, ...]:
        raw = gate.get("prerequisite_modules")

        return TaskDependencyReconstructor._string_list(
            raw,
            "gate.prerequisite_modules",
        )

    @staticmethod
    def _optional_owner(
        mapping: Mapping[str, Any],
    ) -> str | None:
        owner = mapping.get("owner")

        if owner is None:
            return None

        if not isinstance(owner, str) or not owner.strip():
            raise TaskDependencyIntegrityError(
                "owner must be a non-empty string when declared."
            )

        return owner.strip()

    @staticmethod
    def _fingerprint(
        current_gate: str,
        current_task: str,
        current_subtask: str,
        prerequisite_gates: tuple[str, ...],
        prerequisite_subtasks: tuple[str, ...],
        prerequisite_modules: tuple[str, ...],
        dependency_owners: tuple[tuple[str, str], ...],
        blocked_by: tuple[DependencyBlocker, ...],
        conflicts: tuple[str, ...],
        first_valid_work_unit: str,
        status: DependencyResolutionStatus,
    ) -> str:
        payload = {
            "current_gate": current_gate,
            "current_task": current_task,
            "current_subtask": current_subtask,
            "prerequisite_gates": prerequisite_gates,
            "prerequisite_subtasks": prerequisite_subtasks,
            "prerequisite_modules": prerequisite_modules,
            "dependency_owners": dependency_owners,
            "blocked_by": tuple(
                (
                    item.kind,
                    item.dependency_id,
                    item.reason,
                )
                for item in blocked_by
            ),
            "conflicts": conflicts,
            "first_valid_work_unit": first_valid_work_unit,
            "status": status.value,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def reconstruct(self) -> TaskDependencyResolution:
        """Resolve the current valid work unit from canonical state."""

        try:
            execution = ExecutionStateReconstructor(
                self.root
            ).reconstruct()
        except StateReconstructionError as exc:
            raise TaskDependencySourceError(
                "T05 requires a valid T03 execution-state reconstruction."
            ) from exc

        state = self._read_state(self.state_path)

        gate_plans = state.get("gate_plans")
        dependencies = state.get("dependencies")

        if not isinstance(gate_plans, Mapping):
            raise TaskDependencyIntegrityError(
                "state.gate_plans must be an object."
            )

        if not isinstance(dependencies, Mapping):
            raise TaskDependencyIntegrityError(
                "state.dependencies must be an object."
            )

        current_gate = execution.gate_id
        current_task = execution.current_task
        current_subtask = execution.current_subtask
        current_subtask_status = (
            execution.current_subtask_status
        )

        gate = gate_plans.get(current_gate)

        if not isinstance(gate, Mapping):
            raise TaskDependencyIntegrityError(
                f"Current gate missing from gate_plans: {current_gate}"
            )

        subtasks = gate.get("subtasks")

        if not isinstance(subtasks, list) or not subtasks:
            raise TaskDependencyIntegrityError(
                f"gate_plans[{current_gate}].subtasks must be "
                "a non-empty list."
            )

        ordered_subtasks: list[str] = []
        subtask_statuses: dict[str, str] = {}

        for item in subtasks:
            if not isinstance(item, Mapping):
                raise TaskDependencyIntegrityError(
                    "Current gate contains an invalid subtask entry."
                )

            subtask_id = self._required_string(
                item.get("id"),
                "subtask.id",
            )

            status = self._required_string(
                item.get("status"),
                f"subtask[{subtask_id}].status",
            ).upper()

            if subtask_id in subtask_statuses:
                raise TaskDependencyIntegrityError(
                    f"Duplicate subtask: {subtask_id}"
                )

            ordered_subtasks.append(subtask_id)
            subtask_statuses[subtask_id] = status

        if current_subtask not in subtask_statuses:
            raise TaskDependencyConflictError(
                "Current subtask is not present in the authoritative "
                f"gate plan: {current_subtask}"
            )

        if subtask_statuses[current_subtask] == "DONE":
            raise TaskDependencyConflictError(
                "Current subtask is already complete."
            )

        current_index = ordered_subtasks.index(
            current_subtask
        )

        prerequisite_subtasks = tuple(
            ordered_subtasks[:current_index]
        )

        blocked_by: list[DependencyBlocker] = []
        conflicts: list[str] = []

        for subtask_id in prerequisite_subtasks:
            status = subtask_statuses[subtask_id]

            if status != "DONE":
                blocked_by.append(
                    DependencyBlocker(
                        kind="SUBTASK",
                        dependency_id=subtask_id,
                        reason=(
                            "Required prior subtask is not complete."
                        ),
                    )
                )

        nodes = dependencies.get("nodes")

        if not isinstance(nodes, list):
            raise TaskDependencyIntegrityError(
                "dependencies.nodes must be a list."
            )

        node_statuses: dict[str, str] = {}

        for node in nodes:
            if not isinstance(node, Mapping):
                raise TaskDependencyIntegrityError(
                    "dependencies.nodes contains an invalid entry."
                )

            node_id = self._required_string(
                node.get("id"),
                "dependencies.nodes.id",
            )

            status = self._required_string(
                node.get("status"),
                f"dependencies.nodes[{node_id}].status",
            ).upper()

            if node_id in node_statuses:
                raise TaskDependencyIntegrityError(
                    f"Duplicate dependency node: {node_id}"
                )

            node_statuses[node_id] = status

        if current_gate not in node_statuses:
            conflicts.append(
                "Current gate is missing from dependencies.nodes."
            )

        predecessor_graph = self._build_predecessor_graph(
            dependencies.get("edges")
        )

        prerequisite_gates = (
            self._transitive_predecessors(
                current_gate,
                predecessor_graph,
            )
        )

        known_gate_ids = set(gate_plans.keys())

        for gate_id in prerequisite_gates:
            if gate_id not in known_gate_ids:
                conflicts.append(
                    "Dependency references missing gate plan: "
                    f"{gate_id}"
                )
                continue

            prerequisite_gate = gate_plans[gate_id]

            if not isinstance(prerequisite_gate, Mapping):
                conflicts.append(
                    "Dependency gate plan is not an object: "
                    f"{gate_id}"
                )
                continue

            if not self._is_gate_complete(
                prerequisite_gate
            ):
                blocked_by.append(
                    DependencyBlocker(
                        kind="GATE",
                        dependency_id=gate_id,
                        reason=(
                            "Prerequisite gate is not complete."
                        ),
                    )
                )

            graph_status = node_statuses.get(gate_id)

            gate_status = prerequisite_gate.get("status")

            if (
                isinstance(graph_status, str)
                and isinstance(gate_status, str)
                and graph_status
                != gate_status.strip().upper()
            ):
                conflicts.append(
                    "Dependency node status is stale/conflicting "
                    f"for {gate_id}: graph={graph_status}, "
                    f"gate_plan={gate_status.strip().upper()}"
                )

        module_dependencies = self._optional_modules(
            gate
        )

        dependency_owners: list[tuple[str, str]] = []

        gate_owner = self._optional_owner(gate)

        if gate_owner is not None:
            dependency_owners.append(
                ("CURRENT_GATE", gate_owner)
            )

        for gate_id in prerequisite_gates:
            prerequisite_gate = gate_plans.get(gate_id)

            if isinstance(prerequisite_gate, Mapping):
                owner = self._optional_owner(
                    prerequisite_gate
                )

                if owner is not None:
                    dependency_owners.append(
                        (gate_id, owner)
                    )

        for module_id in module_dependencies:
            dependency_owner = gate.get(
                "module_owners",
                {},
            )

            if not isinstance(
                dependency_owner,
                Mapping,
            ):
                raise TaskDependencyIntegrityError(
                    "gate.module_owners must be an object."
                )

            owner = dependency_owner.get(module_id)

            if owner is not None:
                dependency_owners.append(
                    (module_id, self._required_string(
                        owner,
                        f"module_owners[{module_id}]",
                    ))
                )
            else:
                conflicts.append(
                    "Module dependency has no declared owner: "
                    f"{module_id}"
                )

        first_valid_work_unit = (
            f"{current_gate}:{current_subtask}"
        )

        status = (
            DependencyResolutionStatus.BLOCKED
            if blocked_by
            else DependencyResolutionStatus.VALID
        )

        fingerprint = self._fingerprint(
            current_gate,
            current_task,
            current_subtask,
            prerequisite_gates,
            prerequisite_subtasks,
            module_dependencies,
            tuple(dependency_owners),
            tuple(blocked_by),
            tuple(conflicts),
            first_valid_work_unit,
            status,
        )

        return TaskDependencyResolution(
            current_gate=current_gate,
            current_task=current_task,
            current_subtask=current_subtask,
            current_subtask_status=current_subtask_status,
            prerequisite_gates=prerequisite_gates,
            prerequisite_subtasks=prerequisite_subtasks,
            prerequisite_modules=module_dependencies,
            dependency_owners=tuple(
                dependency_owners
            ),
            blocked_by=tuple(blocked_by),
            conflicts=tuple(conflicts),
            first_valid_work_unit=first_valid_work_unit,
            status=status,
            dependency_fingerprint=fingerprint,
            source_state_sha256=execution.source_state_sha256,
        )


def reconstruct_task_dependencies(
    control_center_root: Path | str | None = None,
) -> TaskDependencyResolution:
    """Convenience T05 dependency reconstruction API."""

    return TaskDependencyReconstructor(
        control_center_root
    ).reconstruct()


__all__ = [
    "DependencyBlocker",
    "DependencyResolutionStatus",
    "TaskDependencyConflictError",
    "TaskDependencyError",
    "TaskDependencyIntegrityError",
    "TaskDependencyReconstructor",
    "TaskDependencyResolution",
    "TaskDependencySourceError",
    "reconstruct_task_dependencies",
]
