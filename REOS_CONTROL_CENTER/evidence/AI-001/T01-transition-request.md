# AI-001-T01 — Owner Transition Request

**Project:** HOMIO / REOS  
**Canonical branch:** `reos-development`  
**Subtask:** `AI-001-T01 — Implement AI Gateway`  
**Request date:** 2026-10-26

## Explicit authorization

APPROVAL: AUTHORIZE AI-001-T01 COMPLETION

SCOPE: AI-001-T01 only

## Preconditions

The existing guarded GitHub Actions transition must independently verify the triggering commit, canonical branch, repository owner, clean checkout, current Control Center state, required source files, and required test suites.

The transition must stop on any failed check, stale branch head, missing authorization text, or state mismatch.

## State and governance boundaries

1. Use the existing Control Center `complete-subtask` transition as the sole authority for changing canonical execution state.
2. Do not manually edit `REOS_CONTROL_CENTER/data/state.json`.
3. Do not mark AI-001 acceptance criteria complete through this subtask transition.
4. Preserve `AI-001-AC01` through `AI-001-AC06` as `PENDING`.
5. Complete only `AI-001-T01`; advance to `AI-001-T02` only if the existing controller confirms the transition.
6. Require successful test execution and canonical remote readback before reporting completion.

## Guarded workflow trigger

The owner authorization above is intended to be consumed by the repository's existing guarded workflow. The trigger commit must begin with the exact subject prefix:

`[CONTROL-CENTER-COMPLETE-AI-001-T01]`

This trigger permits an attempt to complete T01 only. It does not authorize acceptance-criteria closure or bypass any validation.

## Retry authorization

The bytecode-safe transition wiring checks passed in GitHub Actions run #326.

I authorize retrying the same guarded AI-001-T01 completion process against the new triggering commit. All existing branch, owner, state, test, file-inventory, and remote-readback safeguards must remain enforced.

This retry does not authorize completion of AI-001-T02 or any AI-001 acceptance criterion.

## Expected result

Completion is valid only after the guarded workflow succeeds, the existing Control Center performs the transition, and the resulting canonical state and evidence are verified by remote readback.
