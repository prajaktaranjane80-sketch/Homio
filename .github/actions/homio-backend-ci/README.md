# HOMIO Backend CI Modules

## Ownership

- `.github/workflows/backend-ci.yml` is the thin orchestration entry point: triggers, permissions, concurrency, dependencies, and reusable-workflow calls only.
- `.github/workflows/reusable-backend-verification.yml` owns the read-only verification job.
- `.github/workflows/reusable-core008-t06-transition.yml` owns the guarded T06 job boundary.
- `verification/` owns read-only compile, contract, finance, tenant, and ACRL regression commands.
- `shared/transition_contract.py` provides read-only canonical-state helpers used by guarded transition modules.
- `transitions/core008-t06/` owns T06 preflight, focused/full regressions, controller invocation, evidence creation, and publish/readback.
- `verification/tests/test_workflow_module_wiring.py` checks important imports and path links.
- `shared/test_transition_contract.py` checks the shared criterion-baseline helper independently.

## GitHub Actions placement

Reusable workflow YAML files must live directly in `.github/workflows/`; subdirectories inside that folder are not supported for reusable workflows. Composite actions and their implementation scripts live under `.github/actions/` in responsibility-based subfolders.

## Authority and security rules

Never edit `REOS_CONTROL_CENTER/data/state.json` directly to complete a task. A guarded transition must verify owner, branch, exact commit SHA, current task, criterion baseline, required source files, controller integrity, handoffs, and snapshot integrity.

The transition must stage only allowlisted files, push without force, and read the canonical branch state back.

Shared helpers must remain read-only. Task-specific criteria, tests, evidence, and publish rules stay inside that task's module folder.

## Adding future modules

Create a task-owned folder for a new responsibility. Add a separate reusable workflow entry point, add its caller only when canonical state identifies that subtask as current, update trigger paths and wiring tests, and use shared helpers only for genuinely common rules.

Do not implement a new task by editing an unrelated subtask module.

CORE-008-T04 and CORE-008-T05 are already DONE. Their historical evidence and Actions runs remain the completion record; their one-shot transition jobs are intentionally not active in the current orchestrator.
