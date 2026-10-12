from __future__ import annotations

from typing import Any

PRE_CODING_PHASE = "PRE-CODING ARCHITECTURE"


def expected_phase_for_gate(state: dict[str, Any]) -> str | None:
    """Resolve the phase from the canonical execution-plan gate.

    Unknown or unregistered gates fail closed: no phase is guessed.
    """
    execution = state.get("execution")
    plan = state.get("execution_plan")
    phases = state.get("phases")

    if not isinstance(execution, dict):
        return None
    if not isinstance(plan, dict) or not isinstance(phases, dict):
        return None

    gate_id = execution.get("current_gate")
    sequence = plan.get("authoritative_sequence")

    if not isinstance(gate_id, str) or not isinstance(sequence, list):
        return None

    registered = any(
        isinstance(step, dict) and step.get("gate") == gate_id
        for step in sequence
    )
    if not registered:
        return None

    if gate_id.startswith(("ARCH-", "REPO-", "ENG-")):
        return PRE_CODING_PHASE

    if gate_id.startswith("CORE-"):
        phase_key = "phase_1"
    elif gate_id.startswith(("AI-", "APP-", "REL-", "SCALE-")):
        phase_key = "phase_2"
    else:
        return None

    phase = phases.get(phase_key)
    return phase.strip() if isinstance(phase, str) and phase.strip() else None


def is_phase_coherent(state: dict[str, Any]) -> bool:
    """Return true only when phases.current matches the registered gate."""
    expected = expected_phase_for_gate(state)
    phases = state.get("phases")

    return (
        expected is not None
        and isinstance(phases, dict)
        and phases.get("current") == expected
    )


def synchronize_current_phase(state: dict[str, Any]) -> bool:
    """Update the derived current-phase projection for a registered gate.

    Returns true when a correction was made. An unknown gate is not changed.
    """
    expected = expected_phase_for_gate(state)
    if expected is None:
        return False

    phases = state.setdefault("phases", {})
    if not isinstance(phases, dict):
        return False

    if phases.get("current") == expected:
        return False

    phases["current"] = expected
    return True