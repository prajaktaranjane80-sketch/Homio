
# AI-001-T09 Transition Request

APPROVAL: AUTHORIZE AI-001-T09 COMPLETION

SCOPE: AI-001-T09 only

## Verification objective

Run the full existing AI platform safety, security, and reliability regression inventory against the exact commit that carries this request. Do not introduce duplicate test modules or duplicate AI platform implementations.

## Required verification

- Verify repository `prajaktaranjane80-sketch/Homio`, branch `reos-development`, the exact triggering commit SHA, and repository-owner authorization.
- Run the canonical Control Center `verify-state` command before the transition.
- Confirm AI-001-T01 through AI-001-T08 are DONE, AI-001-T09 is CURRENT, and AI-001-T10 is PENDING.
- Confirm AI-001-AC01 through AI-001-AC06 remain PENDING.
- Confirm all required AI source and test files exist, and reject obsolete duplicate test paths.
- Compile the existing AI platform Python sources in memory.
- Run the AI agent entrypoint contract tests; require at least 15 passing tests.
- Run all 10 existing AI platform regression modules; require at least 157 passing tests.
- Run the complete ACRL regression suite; require at least 1444 passing tests.
- Recheck the canonical branch HEAD before any task-state mutation.
- Complete AI-001-T09 only through the existing Control Center `complete-subtask` command.
- Verify the controller-created snapshot, canonical state integrity, packet and handoff markers, generated evidence, and remote readback from `reos-development`.
- Fail closed if tests, minimum test counts, ownership checks, branch checks, state integrity, evidence checks, or remote readback fail.

## Scope restrictions

- This request authorizes AI-001-T09 only.
- AI-001-T10 and AI-001-AC01 through AI-001-AC06 remain outside the scope of this transition.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not create another gateway, authorization engine, provider layer, or duplicate test tree.
- Do not enable live provider credentials, production tool execution, or customer-facing AI.
- Do not force-push or bypass branch protections.
- Do not claim completion unless the guarded transition and canonical remote readback both pass.

## Conditional completion

Completion is permitted only after every required verification succeeds on the exact commit containing this request. On success, record the actual test counts, verified code SHA, Actions run URL, source blob SHAs, controller transition, and canonical readback in `T09-safety-security-reliability-evidence.md`.

This request is not evidence that the tests have passed. It authorizes the workflow to run and verify them.
Trigger note: Run guarded AI-001-T09 verification against this exact commit.
