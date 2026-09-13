from __future__ import annotations

"""HOMIO autonomous mission runtime.

Executable bridge between the strategic autonomous master plan and the live
REOS Control Center state. It is deliberately read-only: it must not become a
second controller, roadmap, state authority, or mutation engine.
"""

import argparse
import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[2]
MASTER_PLAN_PATH = ROOT / "HOMIO_AUTONOMOUS_MASTER_PLAN.json"
STATE_PATH = ROOT / "data" / "state.json"

Mode = Literal["HOMIO_BUILDER", "HOMIO_RUNTIME"]


@dataclass(frozen=True, slots=True)
class MissionPosition:
    mode: Mode
    current_gate: str | None
    current_task: str | None
    current_subtask: str | None
    gate_status: str | None
    execution_status: str | None
    next_gate: str | None
    criteria_total: int
    criteria_verified: int
    criteria_pending: int


@dataclass(frozen=True, slots=True)
class SafeAction:
    action_id: str
    kind: str
    target: str
    requires_mutation: bool
    risk: str
    reason: str


@dataclass(frozen=True, slots=True)
class MissionDecision:
    status: Literal["READY", "BLOCKED"]
    position: MissionPosition
    action: SafeAction | None
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    authority: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "position": asdict(self.position),
            "action": asdict(self.action) if self.action else None,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "authority": dict(self.authority),
        }


class AutonomousMissionRuntime:
    """Read-only mission decision engine for HOMIO build/runtime modes."""

    def __init__(
        self,
        *,
        root: Path = ROOT,
        master_plan_path: Path = MASTER_PLAN_PATH,
        state_path: Path = STATE_PATH,
    ) -> None:
        self.root = Path(root).resolve()
        self.master_plan_path = Path(master_plan_path).resolve()
        self.state_path = Path(state_path).resolve()

    @staticmethod
    def _load_json(path: Path, label: str) -> dict[str, Any]:
        if not path.is_file():
            raise RuntimeError(f"{label} missing: {path}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid {label}: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeError(f"{label} must contain a JSON object")
        return value

    @staticmethod
    def _canonical_state_bytes(state: dict[str, Any]) -> bytes:
        clone = copy.deepcopy(state)
        clone.setdefault("integrity", {})["sha256"] = None
        return json.dumps(
            clone,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def _calculate_hash(cls, state: dict[str, Any]) -> str:
        return hashlib.sha256(cls._canonical_state_bytes(state)).hexdigest()

    @classmethod
    def _state_integrity_ok(cls, state: dict[str, Any]) -> bool:
        stored = state.get("integrity", {}).get("sha256")
        return isinstance(stored, str) and stored == cls._calculate_hash(state)

    def _load_authority(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
        plan = self._load_json(self.master_plan_path, "HOMIO autonomous master plan")
        state = self._load_json(self.state_path, "canonical Control Center state")

        authority = plan.get("authority")
        if not isinstance(authority, dict):
            raise RuntimeError("Master plan authority contract is missing")

        if authority.get("canonical_project_state") != "REOS_CONTROL_CENTER/data/state.json":
            raise RuntimeError("Master plan canonical state contract is not canonical")

        if not self._state_integrity_ok(state):
            raise RuntimeError("Canonical state integrity check failed")

        return plan, state, {
            "master_plan": str(self.master_plan_path),
            "canonical_state": str(self.state_path),
            "execution_authority": "reos_control_center.py",
            "mutation_boundary": "ControllerExecutor/ExecutionPipeline",
        }

    @staticmethod
    def _current_sequence_entry(state: dict[str, Any]) -> tuple[dict[str, Any] | None, int]:
        sequence = state.get("execution_plan", {}).get("authoritative_sequence", [])
        if not isinstance(sequence, list):
            return None, 0
        current = [
            entry for entry in sequence
            if isinstance(entry, dict) and entry.get("status") == "CURRENT"
        ]
        return (current[0] if len(current) == 1 else None), len(current)

    @classmethod
    def _next_gate(cls, state: dict[str, Any], current_gate: str | None) -> str | None:
        if not current_gate:
            return None
        sequence = state.get("execution_plan", {}).get("authoritative_sequence", [])
        if not isinstance(sequence, list):
            return None
        for index, entry in enumerate(sequence):
            if isinstance(entry, dict) and entry.get("gate") == current_gate:
                for candidate in sequence[index + 1 :]:
                    if isinstance(candidate, dict):
                        return candidate.get("gate")
                return None
        return None

    @staticmethod
    def _criteria(gate_plan: dict[str, Any]) -> list[dict[str, Any]]:
        value = gate_plan.get("criteria_state", gate_plan.get("acceptance_criteria", []))
        return value if isinstance(value, list) else []

    def _position(self, state: dict[str, Any], mode: Mode):
        execution = state.get("execution", {})
        current_gate = execution.get("current_gate")
        current_task = execution.get("current_task")
        current_subtask = execution.get("current_subtask")

        gate_plan = state.get("gate_plans", {}).get(current_gate, {})
        if not isinstance(gate_plan, dict):
            gate_plan = {}
        criteria = self._criteria(gate_plan)

        verified = sum(
            1 for item in criteria if isinstance(item, dict) and item.get("status") == "VERIFIED"
        )
        pending = sum(
            1 for item in criteria
            if isinstance(item, dict) and item.get("status") in {"PENDING", "UNVERIFIED"}
        )

        blockers: list[str] = []
        warnings: list[str] = []
        plan_current, current_count = self._current_sequence_entry(state)

        if current_count != 1:
            blockers.append("CURRENT_GATE_NOT_UNIQUE")
        if not current_gate:
            blockers.append("CURRENT_GATE_MISSING")
        if not current_subtask:
            blockers.append("CURRENT_SUBTASK_MISSING")
        if plan_current and plan_current.get("gate") != current_gate:
            blockers.append("STATE_PLAN_GATE_MISMATCH")

        if gate_plan.get("status") == "READY_FOR_VALIDATION" and pending:
            warnings.append("Gate reports READY_FOR_VALIDATION while criteria remain pending")

        position = MissionPosition(
            mode=mode,
            current_gate=current_gate,
            current_task=current_task,
            current_subtask=current_subtask,
            gate_status=gate_plan.get("status"),
            execution_status=execution.get("status"),
            next_gate=self._next_gate(state, current_gate),
            criteria_total=len(criteria),
            criteria_verified=verified,
            criteria_pending=pending,
        )
        return position, tuple(blockers), tuple(warnings)

    @staticmethod
    def _action(position: MissionPosition) -> SafeAction | None:
        if not position.current_gate or not position.current_subtask:
            return None
        return SafeAction(
            action_id=f"inspect:{position.current_subtask}",
            kind="INSPECT_CURRENT_SUBTASK",
            target=position.current_subtask,
            requires_mutation=False,
            risk="LOW",
            reason=(
                "Resolve repository evidence, dependencies, contracts and existing implementation "
                "before proposing any mutation for the authoritative current subtask."
            ),
        )

    def decide(self, mode: Mode = "HOMIO_BUILDER") -> MissionDecision:
        plan, state, authority = self._load_authority()
        position, blockers, warnings = self._position(state, mode)

        if blockers:
            return MissionDecision("BLOCKED", position, None, blockers, warnings, authority)

        if not isinstance(plan.get("phases"), list) or not plan["phases"]:
            return MissionDecision(
                "BLOCKED",
                position,
                None,
                ("MASTER_PLAN_PHASES_MISSING",),
                warnings,
                authority,
            )

        return MissionDecision(
            "READY",
            position,
            self._action(position),
            (),
            warnings,
            authority,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HOMIO autonomous mission decision runtime")
    parser.add_argument(
        "--mode",
        choices=("HOMIO_BUILDER", "HOMIO_RUNTIME"),
        default="HOMIO_BUILDER",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        decision = AutonomousMissionRuntime().decide(mode=args.mode)
    except RuntimeError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))
    return 0 if decision.status == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
