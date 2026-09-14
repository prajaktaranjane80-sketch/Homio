"""REOS L3 Control Plane.

This module is the authoritative integration boundary between:

```
REOS_CONTROL_CENTER
    |
    +-- canonical state
    +-- lifecycle authority
    +-- gate/task/subtask authority
    +-- approval authority
    +-- transition authority
    |
    v
L3 CONTROL PLANE
    |
    +-- state integrity
    +-- authority verification
    +-- execution-position verification
    +-- ACRL continuity compatibility
    +-- AUTONOMY_ENGINE integration compatibility
    +-- fail-closed decisions
    |
    v
existing REOS capabilities
```

## IMPORTANT

This module intentionally does NOT become another runtime, executor,
state store, roadmap, ACRL implementation, or AI agent.

It coordinates existing capabilities.

Authority hierarchy:

```
state.json
    >
REOS_CONTROL_CENTER lifecycle
    >
L3 Control Plane
    >
AUTONOMY_ENGINE / ACRL execution intelligence
```

The control plane may ALLOW or BLOCK an operation.

It must never silently grant authority that does not already exist.
"""

from **future** import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

class ControlPlaneDecision(str, Enum):
"""Final L3 decision."""

```
ALLOW = "ALLOW"
BLOCK = "BLOCK"
```

class ControlPlaneBlockReason(str, Enum):
"""Machine-readable reasons for refusing control-plane progress."""

```
CANONICAL_STATE_MISSING = "CANONICAL_STATE_MISSING"
CANONICAL_STATE_INVALID = "CANONICAL_STATE_INVALID"
CANONICAL_STATE_INTEGRITY_FAILURE = "CANONICAL_STATE_INTEGRITY_FAILURE"
CANONICAL_AUTHORITY_INVALID = "CANONICAL_AUTHORITY_INVALID"

EXECUTION_POSITION_INVALID = "EXECUTION_POSITION_INVALID"
CURRENT_GATE_MISSING = "CURRENT_GATE_MISSING"
CURRENT_TASK_MISSING = "CURRENT_TASK_MISSING"

ACRL_UNAVAILABLE = "ACRL_UNAVAILABLE"
ACRL_CONTEXT_INVALID = "ACRL_CONTEXT_INVALID"

AUTONOMY_ENGINE_INTEGRATION_INVALID = (
    "AUTONOMY_ENGINE_INTEGRATION_INVALID"
)

ARCHITECTURE_NOT_LOCKED = "ARCHITECTURE_NOT_LOCKED"
AUTHORITY_BOUNDARY_VIOLATION = "AUTHORITY_BOUNDARY_VIOLATION"

POSTFLIGHT_INVALID = "POSTFLIGHT_INVALID"

UNKNOWN = "UNKNOWN"
```

@dataclass(frozen=True)
class ControlPlaneSnapshot:
"""Immutable snapshot of authoritative execution position."""

```
controller: str
canonical_state: str
current_gate: str
current_task: str
current_subtask: str | None
state_hash: str | None
architecture_locked: bool
authority_valid: bool

def to_dict(self) -> dict[str, Any]:
    return {
        "controller": self.controller,
        "canonical_state": self.canonical_state,
        "current_gate": self.current_gate,
        "current_task": self.current_task,
        "current_subtask": self.current_subtask,
        "state_hash": self.state_hash,
        "architecture_locked": self.architecture_locked,
        "authority_valid": self.authority_valid,
    }
```

@dataclass(frozen=True)
class ControlPlaneResult:
"""Internal immutable result."""

```
decision: ControlPlaneDecision
reason: str
block_reason: ControlPlaneBlockReason | None = None
evidence: Mapping[str, Any] = ()

@property
def allowed(self) -> bool:
    return self.decision is ControlPlaneDecision.ALLOW

def to_dict(self) -> dict[str, Any]:
    return {
        "decision": self.decision.value,
        "allowed": self.allowed,
        "reason": self.reason,
        "block_reason": (
            self.block_reason.value
            if self.block_reason is not None
            else None
        ),
        "evidence": dict(self.evidence),
    }
```

class ControlPlane:
"""Authoritative L3 coordination boundary.

```
The class is deliberately dependency-light.

It does not instantiate or own:
- AgentRuntime
- ExecutionCoordinator
- ControlledMutationAdapter
- ACRL implementation
- another state store

Existing capabilities are injected or supplied as already-authorized
results.

This prevents L3 from becoming a duplicate autonomy stack.
"""

CONTROLLER_NAME = "REOS_CONTROL_CENTER"
AUTONOMY_ENGINE_NAME = "AUTONOMY_ENGINE"

def __init__(
    self,
    *,
    canonical_state_path: Path,
    state_loader: Any,
    state_hasher: Any,
    integration_verifier: Any,
) -> None:
    self._canonical_state_path = Path(canonical_state_path)
    self._state_loader = state_loader
    self._state_hasher = state_hasher
    self._integration_verifier = integration_verifier

# ------------------------------------------------------------------
# Canonical authority
# ------------------------------------------------------------------

def verify_canonical_state_path(self) -> ControlPlaneResult:
    """Verify that the configured state path is canonical."""

    expected_name = Path("data") / "state.json"

    try:
        relative = self._canonical_state_path.resolve().relative_to(
            self._canonical_state_path.parent.parent.resolve()
        )
    except ValueError:
        relative = self._canonical_state_path

    if (
        self._canonical_state_path.name != expected_name.name
        or self._canonical_state_path.parent.name != expected_name.parent.name
    ):
        return self._block(
            ControlPlaneBlockReason.CANONICAL_AUTHORITY_INVALID,
            "Configured canonical state path is not data/state.json.",
            {
                "configured_path": str(self._canonical_state_path),
            },
        )

    return self._allow(
        "Canonical state path resolves to REOS_CONTROL_CENTER/data/state.json.",
        {
            "canonical_state": str(self._canonical_state_path),
            "relative_check": str(relative),
        },
    )

def load_and_verify_state(self) -> tuple[ControlPlaneResult, dict[str, Any] | None]:
    """Load state through the existing controller loader.

    The loader remains responsible for actual state parsing.
    L3 owns the decision about whether the result is trustworthy.
    """

    path_result = self.verify_canonical_state_path()

    if not path_result.allowed:
        return path_result, None

    if not self._canonical_state_path.exists():
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_MISSING,
            "Canonical state.json does not exist.",
            {
                "canonical_state": str(self._canonical_state_path),
            },
        )
        return result, None

    try:
        state = self._state_loader()
    except SystemExit as exc:
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_INVALID,
            str(exc),
            {
                "canonical_state": str(self._canonical_state_path),
            },
        )
        return result, None
    except Exception as exc:
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_INVALID,
            "Canonical state could not be loaded safely.",
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        return result, None

    if not isinstance(state, dict):
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_INVALID,
            "Canonical state root must be a JSON object.",
            {
                "actual_type": type(state).__name__,
            },
        )
        return result, None

    integrity = state.get("integrity")

    if not isinstance(integrity, dict):
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_INTEGRITY_FAILURE,
            "Canonical state has no valid integrity metadata.",
            {},
        )
        return result, None

    stored_hash = integrity.get("sha256")

    if not isinstance(stored_hash, str) or not stored_hash.strip():
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_INTEGRITY_FAILURE,
            "Canonical state integrity hash is missing.",
            {},
        )
        return result, None

    try:
        calculated_hash = self._state_hasher(state)
    except Exception as exc:
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_INTEGRITY_FAILURE,
            "Canonical state hash calculation failed.",
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        return result, None

    if stored_hash != calculated_hash:
        result = self._block(
            ControlPlaneBlockReason.CANONICAL_STATE_INTEGRITY_FAILURE,
            "Canonical state integrity verification failed.",
            {
                "stored_hash": stored_hash,
                "calculated_hash": calculated_hash,
            },
        )
        return result, None

    return (
        self._allow(
            "Canonical state loaded and integrity verified.",
            {
                "canonical_state": str(self._canonical_state_path),
                "state_hash": calculated_hash,
            },
        ),
        state,
    )

# ------------------------------------------------------------------
# Authority / execution position
# ------------------------------------------------------------------

def verify_authority(
    self,
    state: Mapping[str, Any],
) -> ControlPlaneResult:
    """Verify that state contains the authoritative execution model."""

    constitution = state.get("constitution")

    if not isinstance(constitution, Mapping):
        return self._block(
            ControlPlaneBlockReason.CANONICAL_AUTHORITY_INVALID,
            "Canonical state has no constitution metadata.",
            {},
        )

    if constitution.get("canonical_source") != "data/state.json":
        return self._block(
            ControlPlaneBlockReason.CANONICAL_AUTHORITY_INVALID,
            "Canonical source is not data/state.json.",
            {
                "canonical_source": constitution.get("canonical_source"),
            },
        )

    if constitution.get("single_source_of_truth") is not True:
        return self._block(
            ControlPlaneBlockReason.CANONICAL_AUTHORITY_INVALID,
            "Canonical state does not declare a single source of truth.",
            {},
        )

    if constitution.get("gate_subtasks_are_authoritative") is not True:
        return self._block(
            ControlPlaneBlockReason.AUTHORITY_BOUNDARY_VIOLATION,
            "Gate subtasks are not declared authoritative.",
            {},
        )

    if constitution.get("acceptance_criteria_are_authoritative") is not True:
        return self._block(
            ControlPlaneBlockReason.AUTHORITY_BOUNDARY_VIOLATION,
            "Acceptance criteria are not declared authoritative.",
            {},
        )

    return self._allow(
        "Canonical authority model is valid.",
        {
            "canonical_source": "data/state.json",
            "single_source_of_truth": True,
            "gate_subtasks_authoritative": True,
            "criteria_authoritative": True,
        },
    )

def verify_execution_position(
    self,
    state: Mapping[str, Any],
) -> tuple[ControlPlaneResult, ControlPlaneSnapshot | None]:
    """Resolve the authoritative current execution position."""

    execution = state.get("execution")

    if not isinstance(execution, Mapping):
        return (
            self._block(
                ControlPlaneBlockReason.EXECUTION_POSITION_INVALID,
                "Execution authority is missing from canonical state.",
                {},
            ),
            None,
        )

    current_gate = execution.get("current_gate")
    current_task = execution.get("current_task")

    if not isinstance(current_gate, str) or not current_gate.strip():
        return (
            self._block(
                ControlPlaneBlockReason.CURRENT_GATE_MISSING,
                "Canonical state has no current gate.",
                {},
            ),
            None,
        )

    if not isinstance(current_task, str) or not current_task.strip():
        return (
            self._block(
                ControlPlaneBlockReason.CURRENT_TASK_MISSING,
                "Canonical state has no current task.",
                {},
            ),
            None,
        )

    current_subtask = execution.get("current_subtask")

    architecture = state.get("architecture")
    architecture_locked = False

    if isinstance(architecture, Mapping):
        architecture_locked = architecture.get("locked") is True

    integrity = state.get("integrity")

    state_hash = None
    if isinstance(integrity, Mapping):
        value = integrity.get("sha256")
        if isinstance(value, str):
            state_hash = value

    snapshot = ControlPlaneSnapshot(
        controller=self.CONTROLLER_NAME,
        canonical_state=str(self._canonical_state_path),
        current_gate=current_gate,
        current_task=current_task,
        current_subtask=(
            current_subtask
            if isinstance(current_subtask, str)
            else None
        ),
        state_hash=state_hash,
        architecture_locked=architecture_locked,
        authority_valid=True,
    )

    return (
        self._allow(
            "Authoritative execution position resolved.",
            snapshot.to_dict(),
        ),
        snapshot,
    )

# ------------------------------------------------------------------
# Existing AUTONOMY_ENGINE integration contract
# ------------------------------------------------------------------

def verify_autonomy_engine_integration(self) -> ControlPlaneResult:
    """Reuse the existing integration-lock capability.

    L3 does not duplicate the integration contract.
    """

    try:
        result = self._integration_verifier()
    except Exception as exc:
        return self._block(
            ControlPlaneBlockReason.AUTONOMY_ENGINE_INTEGRATION_INVALID,
            "AUTONOMY_ENGINE integration verification failed.",
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )

    allowed = getattr(result, "allowed", False)

    if allowed is not True:
        return self._block(
            ControlPlaneBlockReason.AUTONOMY_ENGINE_INTEGRATION_INVALID,
            "Existing AUTONOMY_ENGINE integration contract is not compatible.",
            {
                "integration_result": (
                    result.to_dict()
                    if hasattr(result, "to_dict")
                    else str(result)
                ),
            },
        )

    evidence = (
        result.to_dict()
        if hasattr(result, "to_dict")
        else {"integration_result": str(result)}
    )

    return self._allow(
        "Existing AUTONOMY_ENGINE integration contract is compatible.",
        evidence,
    )

# ------------------------------------------------------------------
# Full control-plane preflight
# ------------------------------------------------------------------

def preflight(self) -> ControlPlaneResult:
    """Run the complete non-mutating L3 preflight.

    Order is intentional:

        canonical path
            ->
        state load
            ->
        state integrity
            ->
        authority
            ->
        execution position
            ->
        architecture boundary
            ->
        existing AE integration lock

    No mutation occurs in this method.
    """

    state_result, state = self.load_and_verify_state()

    if not state_result.allowed or state is None:
        return state_result

    authority_result = self.verify_authority(state)

    if not authority_result.allowed:
        return authority_result

    position_result, snapshot = self.verify_execution_position(state)

    if not position_result.allowed or snapshot is None:
        return position_result

    if not snapshot.architecture_locked:
        return self._block(
            ControlPlaneBlockReason.ARCHITECTURE_NOT_LOCKED,
            "Architecture is not locked; autonomous control must fail closed.",
            snapshot.to_dict(),
        )

    integration_result = self.verify_autonomy_engine_integration()

    if not integration_result.allowed:
        return integration_result

    return self._allow(
        "L3 control-plane preflight passed.",
        {
            "controller": self.CONTROLLER_NAME,
            "canonical_state": str(self._canonical_state_path),
            "current_gate": snapshot.current_gate,
            "current_task": snapshot.current_task,
            "current_subtask": snapshot.current_subtask,
            "architecture_locked": snapshot.architecture_locked,
            "state_integrity_verified": True,
            "authority_verified": True,
            "autonomy_engine_integration_verified": True,
            "mutation_performed": False,
        },
    )

# ------------------------------------------------------------------
# Postflight
# ------------------------------------------------------------------

def verify_postflight(
    self,
    *,
    evidence_complete: bool,
    provenance_valid: bool,
    state_consistent: bool,
) -> ControlPlaneResult:
    """Verify execution postflight without performing execution itself."""

    checks = {
        "evidence_complete": evidence_complete,
        "provenance_valid": provenance_valid,
        "state_consistent": state_consistent,
    }

    if not all(checks.values()):
        return self._block(
            ControlPlaneBlockReason.POSTFLIGHT_INVALID,
            "Postflight verification failed; control plane refuses continuation.",
            checks,
        )

    state_result, state = self.load_and_verify_state()

    if not state_result.allowed or state is None:
        return state_result

    authority_result = self.verify_authority(state)

    if not authority_result.allowed:
        return authority_result

    return self._allow(
        "Postflight verification passed and canonical state remains authoritative.",
        {
            **checks,
            "canonical_state_reverified": True,
            "mutation_performed_by_control_plane": False,
        },
    )

# ------------------------------------------------------------------
# Internal result constructors
# ------------------------------------------------------------------

@staticmethod
def _allow(
    reason: str,
    evidence: Mapping[str, Any],
) -> ControlPlaneResult:
    return ControlPlaneResult(
        decision=ControlPlaneDecision.ALLOW,
        reason=reason,
        block_reason=None,
        evidence=dict(evidence),
    )

@staticmethod
def _block(
    block_reason: ControlPlaneBlockReason,
    reason: str,
    evidence: Mapping[str, Any],
) -> ControlPlaneResult:
    return ControlPlaneResult(
        decision=ControlPlaneDecision.BLOCK,
        reason=reason,
        block_reason=block_reason,
        evidence=dict(evidence),
    )
```

**all** = [
"ControlPlane",
"ControlPlaneBlockReason",
"ControlPlaneDecision",
"ControlPlaneResult",
"ControlPlaneSnapshot",
]
