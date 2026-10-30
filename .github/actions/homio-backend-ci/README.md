# HOMIO Backend CI Modules

## Ownership

- `.github/workflows/backend-ci.yml` is the thin orchestration entry point: triggers, permissions, concurrency, dependencies, and reusable-workflow calls only.
- `.github/workflows/reusable-backend-verification.yml` owns the read-only verification job.
- `.github/workflows/reusable-core008-t06-transition.yml` owns the guarded T06 job boundary.
- `verification/` owns read-only compile, contract, finance, tenant, and ACRL regression commands.
- `shared/transition_contract.py` provides read-only canonical-state helpers used by guarded transition modules.
- `transitions/core008-t06/` owns T06 preflight, focused/full regressions, controller invocation, evidence creation, and publish/readback.
- `verification/tests/test_workflow_module_wiring.py` checks existing imports and path links.
- `verification/tests/test_pull_request_governance.py` locks the PR trigger, required-check contract, permissions, exact-commit checkout, and push-only transition guards.
- `shared/test_transition_contract.py` checks the shared criterion-baseline helper independently.

## GitHub Actions placement

Reusable workflow YAML files must live directly in `.github/workflows/`; subdirectories inside that folder are not supported for reusable workflows. Composite actions and their implementation scripts live under `.github/actions/` in responsibility-based subfolders.

## Pull-request verification contract

The canonical backend workflow must run on every pull request targeting `reos-development`. The PR trigger intentionally includes the `"**"` path so that required verification is not silently skipped by a changed-file filter. The push trigger remains limited to the repository's owned backend, frontend, evidence, state, and workflow paths.

The read-only verification entry point is:

`Backend, T21, and ACRL runtime verification / Backend, T21, and ACRL runtime verification`

This exact check context was read from the GitHub Actions check-runs API for the verified backend CI run. It is the required status check to select in the repository ruleset. The job checks out the exact triggering commit via `github.sha`, so its result is bound to the triggering commit (including the PR test-merge commit when GitHub supplies one).

The PR workflow has read-only `contents` permission. Control Center transition, acceptance-validation, and approval jobs remain guarded by push event, canonical branch, and their exact Control Center commit prefixes. They must not run from a pull request.

## Repository ruleset — administrator configuration

GitHub repository settings are not versioned by this repository and are not changed by a successful Actions run. A repository administrator must create and verify this ruleset separately.

Open:

`https://github.com/prajaktaranjane80-sketch/Homio/settings/rules`

Create a **branch ruleset** with these settings:

| Setting | Required configuration |
|---|---|
| Ruleset name | `HOMIO-reos-development-protection` |
| Enforcement status | Active |
| Target branch | Include `reos-development` |
| Require a pull request before merging | Enabled |
| Required approvals | 0 for a single-maintainer repository; increase when an independent reviewer is available |
| Require status checks to pass | Enabled |
| Required status check | `Backend, T21, and ACRL runtime verification / Backend, T21, and ACRL runtime verification` |
| Expected source | GitHub Actions, when the selector offers it |
| Require branches to be up to date | Enabled (strict required-check policy) |
| Require conversation resolution | Enabled |
| Block force pushes | Enabled |
| Restrict deletions | Enabled |
| Bypass list | Empty unless a documented emergency role is explicitly approved |

Do not enable a merge queue until this workflow also handles the `merge_group` event and that event has its own verified required-check run. Do not require production deployments as a merge check until a real protected production deployment workflow exists.

When GitHub does not offer the required check in the ruleset selector, first open a test pull request against `reos-development` and allow the backend verification job to complete. Then select the exact check name above. A successful push run alone does not prove PR check enforcement.

After saving the ruleset, verify that the ruleset is Active and that branch protection reports the expected required check. Do not report protection as enabled until the settings are read back.

## Authority and security rules

Never edit `REOS_CONTROL_CENTER/data/state.json` directly to complete a task. A guarded transition must verify owner, branch, exact commit SHA, current task, criterion baseline, required source files, controller integrity, handoffs, and snapshot integrity.

The transition must stage only allowlisted files, push without force, and read the canonical branch state back.

Shared helpers must remain read-only. Task-specific criteria, tests, evidence, and publish rules stay inside that task's module folder.

## Adding future modules

Create a task-owned folder for a new responsibility. Add a separate reusable workflow entry point, add its caller only when canonical state identifies that subtask as current, update trigger paths and wiring tests, and use shared helpers only for genuinely common rules.

Do not implement a new task by editing an unrelated subtask module.

CORE-008-T04 and CORE-008-T05 are already DONE. Their historical evidence and Actions runs remain the completion record; their one-shot transition jobs are intentionally not active in the current orchestrator.
