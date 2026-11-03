from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class AuthorityExecutionProjection:
    """Validated, minimal execution projection from canonical state."""

    state_integrity_sha256: str

    current_gate: str
    current_gate_status: str

    current_task: str
    current_subtask: str
    current_subtask_status: str

    execution_status: str
    current_acceptance_criteria: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "state_integrity_sha256": self.state_integrity_sha256,
            "current_gate": self.current_gate,
            "current_gate_status": self.current_gate_status,
            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "current_subtask_status": self.current_subtask_status,
            "execution_status": self.execution_status,
            "current_acceptance_criteria": list(
                self.current_acceptance_criteria
            ),
        }


class AuthorityBridge:
    """Read-only bridge to the sole canonical REOS execution state.

    Responsibilities:
    - Validate canonical state location and integrity.
    - Validate frozen architecture authority.
    - Validate current execution against its gate-plan projection.
    - Expose only the minimal execution context needed by ACRL.

    This bridge:
    - Does not create or authorize tasks.
    - Does not mutate state.json.
    - Does not select a new task.
    - Does not create a second state store.
    - Does not claim that local state proves live GitHub freshness.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.state_path = self.project_root / "data" / "state.json"

        self._authority = {
            "project": "HOMIO / REOS",
            "architecture_authority": "FROZEN_APPROVED_ARCHITECTURE",
            "roadmap_authority": "REOS_CONTROL_CENTER",
            "execution_state_authority": (
                "REOS_CONTROL_CENTER/data/state.json"
            ),
            "code_authority": "GIT_REPOSITORY",
            "continuity_authority": "DERIVED_FROM_EXECUTION_STATE",
            "chat_authority": "NONE",
            "schema_version": "1.0",
        }

        self._execution_projection: (
            AuthorityExecutionProjection | None
        ) = None

    @staticmethod
    def _reject_nonstandard_json_constant(value: str) -> None:
        raise ValueError(
            f"Non-standard JSON constant is not allowed: {value}"
        )

    @staticmethod
    def _required_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Canonical execution field is missing: {field_name}"
            )

        return value.strip()

    @staticmethod
    def _canonical_state_hash(state: dict[str, Any]) -> str:
        """Match the existing Control Center integrity algorithm."""

        clone = deepcopy(state)

        integrity = clone.get("integrity")

        if not isinstance(integrity, dict):
            raise ValueError(
                "Canonical state integrity object is missing."
            )

        integrity["sha256"] = None

        canonical = json.dumps(
            clone,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

        return hashlib.sha256(canonical).hexdigest()

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            raise ValueError(
                f"Canonical REOS state.json is missing: {self.state_path}"
            )

        try:
            raw_text = self.state_path.read_text(
                encoding="utf-8-sig"
            )

            state = json.loads(
                raw_text,
                parse_constant=self._reject_nonstandard_json_constant,
            )

        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Unable to read valid canonical state.json: {exc}"
            ) from exc

        if not isinstance(state, dict):
            raise ValueError(
                "Canonical state.json root must be a JSON object."
            )

        return state

    def _validate_state_integrity(
        self,
        state: dict[str, Any],
    ) -> str:
        integrity = state.get("integrity")

        if not isinstance(integrity, dict):
            raise ValueError(
                "Canonical state integrity object is missing."
            )

        stored_hash = integrity.get("sha256")

        if (
            not isinstance(stored_hash, str)
            or not _SHA256_PATTERN.fullmatch(stored_hash)
        ):
            raise ValueError(
                "Canonical state integrity SHA-256 is invalid."
            )

        calculated_hash = self._canonical_state_hash(state)

        if calculated_hash != stored_hash:
            raise ValueError(
                "Canonical state integrity check failed."
            )

        return stored_hash

    def _validate_authority(
        self,
        state: dict[str, Any],
    ) -> None:
        constitution = state.get("constitution")

        if not isinstance(constitution, dict):
            raise ValueError(
                "Canonical state constitution is missing."
            )

        if constitution.get("canonical_source") != "data/state.json":
            raise ValueError(
                "Canonical state source declaration is invalid."
            )

        architecture = state.get("architecture")

        if not isinstance(architecture, dict):
            raise ValueError(
                "Canonical architecture registry is missing."
            )

        if architecture.get("locked") is not True:
            raise ValueError(
                "Approved architecture is not locked."
            )

        approved_architecture = architecture.get("approved")

        if (
            not isinstance(approved_architecture, list)
            or not approved_architecture
        ):
            raise ValueError(
                "Approved architecture registry is empty or invalid."
            )

    def _build_execution_projection(
        self,
        state: dict[str, Any],
        state_hash: str,
    ) -> AuthorityExecutionProjection:
        execution = state.get("execution")

        if not isinstance(execution, dict):
            raise ValueError(
                "Canonical execution projection is missing."
            )

        current_gate = self._required_text(
            execution.get("current_gate"),
            "execution.current_gate",
        )

        current_task = self._required_text(
            execution.get("current_task"),
            "execution.current_task",
        )

        current_subtask = self._required_text(
            execution.get("current_subtask"),
            "execution.current_subtask",
        )

        execution_status = self._required_text(
            execution.get("status"),
            "execution.status",
        )

        raw_criteria = execution.get(
            "current_acceptance_criteria"
        )

        if (
            not isinstance(raw_criteria, list)
            or not raw_criteria
            or any(
                not isinstance(item, str) or not item.strip()
                for item in raw_criteria
            )
        ):
            raise ValueError(
                "Current acceptance criteria are missing or invalid."
            )

        criteria = tuple(
            item.strip()
            for item in raw_criteria
        )

        gate_plans = state.get("gate_plans")

        if not isinstance(gate_plans, dict):
            raise ValueError(
                "Canonical gate_plans registry is missing."
            )

        gate_plan = gate_plans.get(current_gate)

        if not isinstance(gate_plan, dict):
            raise ValueError(
                "Current execution gate has no matching gate plan."
            )

        gate_status = self._required_text(
            gate_plan.get("status"),
            "gate_plans.current_gate.status",
        )

        if gate_status != "CURRENT":
            raise ValueError(
                "Current execution gate and gate-plan status disagree."
            )

        gate_current_subtask = self._required_text(
            gate_plan.get("current_subtask"),
            "gate_plans.current_gate.current_subtask",
        )

        if gate_current_subtask != current_subtask:
            raise ValueError(
                "Current subtask mismatch between execution and gate plan."
            )

        subtasks = gate_plan.get("subtasks")

        if not isinstance(subtasks, list):
            raise ValueError(
                "Current gate subtask registry is invalid."
            )

        matches = [
            item
            for item in subtasks
            if isinstance(item, dict)
            and item.get("id") == current_subtask
        ]

        if len(matches) != 1:
            raise ValueError(
                "Current subtask must resolve to exactly one gate-plan item."
            )

        subtask_status = self._required_text(
            matches[0].get("status"),
            "gate_plans.current_subtask.status",
        )

        return AuthorityExecutionProjection(
            state_integrity_sha256=state_hash,
            current_gate=current_gate,
            current_gate_status=gate_status,
            current_task=current_task,
            current_subtask=current_subtask,
            current_subtask_status=subtask_status,
            execution_status=execution_status,
            current_acceptance_criteria=criteria,
        )

    def validate(self) -> None:
        """Validate one fresh read of the canonical local state."""

        self._execution_projection = None

        if (
            self._authority["architecture_authority"]
            != "FROZEN_APPROVED_ARCHITECTURE"
        ):
            raise ValueError(
                "Architecture authority mismatch."
            )

        if (
            self._authority["roadmap_authority"]
            != "REOS_CONTROL_CENTER"
        ):
            raise ValueError(
                "Roadmap authority mismatch."
            )

        if (
            self._authority["execution_state_authority"]
            != "REOS_CONTROL_CENTER/data/state.json"
        ):
            raise ValueError(
                "Execution-state authority mismatch."
            )

        if self._authority["code_authority"] != "GIT_REPOSITORY":
            raise ValueError(
                "Code authority mismatch."
            )

        if (
            self._authority["continuity_authority"]
            != "DERIVED_FROM_EXECUTION_STATE"
        ):
            raise ValueError(
                "Continuity authority mismatch."
            )

        if self._authority["chat_authority"] != "NONE":
            raise ValueError(
                "Chat cannot be an authority source."
            )

        state = self._load_state()
        state_hash = self._validate_state_integrity(state)

        self._validate_authority(state)

        self._execution_projection = (
            self._build_execution_projection(
                state,
                state_hash,
            )
        )

    def as_dict(self) -> dict[str, str]:
        """Return immutable authority labels, not execution state."""

        return dict(self._authority)

    def execution_projection(
        self,
    ) -> AuthorityExecutionProjection:
        """Return the validated compact execution projection."""

        if self._execution_projection is None:
            raise RuntimeError(
                "AuthorityBridge.validate() must succeed before "
                "execution_projection() is read."
            )

        return self._execution_projection


__all__ = [
    "AuthorityBridge",
    "AuthorityExecutionProjection",
]
