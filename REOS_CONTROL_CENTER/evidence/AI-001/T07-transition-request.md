# AI-001-T07 Transition Request

APPROVAL: AUTHORIZE AI-001-T07 COMPLETION

SCOPE: AI-001-T07 only

## Verification Reference

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Latest successful baseline run: [40452345208](https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/40452345208)
- Baseline commit: `ae7885521ce66371e28ca72c9e0bd6d1c456d0e1`
- Baseline AI entrypoint contract tests: 15 passed
- Baseline AI platform tests including T07 cost controls: 151 passed
- Baseline complete ACRL suite: 1444 passed
- Implementation module: `AUTONOMY_ENGINE/ai_platform/cost_control.py`
- Canonical T07 tests: `AUTONOMY_ENGINE/ai_platform/tests/test_cost_control.py`
- Gateway accounting interface: existing `UsageControlPort`
- Completion route: existing Control Center `complete-subtask`

The baseline run verifies its own commit only. It does not complete AI-001-T07. The guarded transition must rerun all required verification against the exact commit carrying this request.

## Required Transition Checks

- Verify the repository owner, canonical branch, exact triggering commit SHA, and authorized commit-message prefix.
- Verify that the canonical branch HEAD has not moved.
- Run Control Center `verify-state` before any transition.
- Confirm AI-001-T01 through AI-001-T06 are DONE and AI-001-T07 is CURRENT.
- Confirm AI-001-T08 through AI-001-T10 are PENDING.
- Confirm AI-001-AC01 through AI-001-AC06 remain PENDING.
- Compile all Python sources in the AI platform in memory.
- Run the AI entrypoint contract tests.
- Run all canonical AI platform tests, including cost-control and usage-accounting tests.
- Run the complete ACRL regression suite.
- Verify that cost-control tests cover persistent ledger readback, tenant isolation, concurrent quota reservations, idempotency, settlement, release, conservative usage estimates, and over-budget accounting.
- Complete T07 only through the existing Control Center `complete-subtask` command.
- Verify state integrity, the controller-created snapshot, packet and handoff markers, generated evidence, and canonical remote readback.
- Fail closed if any required test, state check, ownership check, or readback fails.

## Scope Restrictions

- This request authorizes AI-001-T07 only.
- AI-001-T08, T09, T10 and all AI-001 gate acceptance criteria remain outside this request.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not create another usage-control port or duplicate gateway accounting path.
- Do not treat a single-host SQLite adapter as a distributed multi-replica quota ledger.
- Do not enable live provider credentials or production/customer-facing AI.
- Do not force-push or bypass the canonical Control Center.
- Do not claim completion unless the guarded transition and canonical readback pass.

## Final Authorization

The owner authorizes the guarded AI-001-T07 completion workflow to validate the exact commit containing this request. Completion is conditional on every required verification succeeding. The workflow must record actual evidence and preserve AI-001-AC01 through AI-001-AC06 as PENDING.
