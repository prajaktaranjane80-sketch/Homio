# Shared backend CI contracts

`transition_contract.py` contains read-only helpers for guarded Control Center transitions. It may read and validate canonical state, but it must never write `state.json`, complete a subtask, or mutate handoffs.

State mutation remains the responsibility of `REOS_CONTROL_CENTER/reos_control_center.py`.

Add a helper here only when multiple transition modules genuinely share the same rule. Task-specific criteria, test commands, evidence format, and write allowlists stay inside that task's own module.
