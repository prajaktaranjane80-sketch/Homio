# AI-001-T08 Transition Request

APPROVAL: AUTHORIZE AI-001-T08 COMPLETION

SCOPE: AI-001-T08 only

## Verification Reference

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Successful baseline Actions run: [40455043930](https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/40455043930)
- Baseline commit: `d4f43ca5ac6d879ac85cc08e516ee4306f846245`
- AI entrypoint contract tests: 15 passed
- AI platform tests including observability and fallback: 157 passed
- Complete ACRL regression suite: 1444 passed
- Gateway: existing `AUTONOMY_ENGINE/ai_platform/model_gateway.py`
- Structured telemetry: `AUTONOMY_ENGINE/ai_platform/observability.py`
- Fallback configuration: existing `GatewaySettings`
- Interfaces: existing `ObservabilityPort`, `ModelRegistryPort`, and `ProviderResolverPort`

The baseline run verifies its own commit only. It does not complete AI-001-T08. The guarded transition must rerun all required verification against the exact commit carrying this request.

## Required Transition Checks

- Verify the repository owner, canonical branch, exact triggering commit SHA, and authorized commit-message prefix.
- Verify that the canonical branch HEAD has not moved.
- Run Control Center `verify-state` before any transition.
- Confirm AI-001-T01 through AI-001-T07 are DONE and AI-001-T08 is CURRENT.
- Confirm AI-001-T09 and AI-001-T10 are PENDING.
- Confirm AI-001-AC01 through AI-001-AC06 remain PENDING.
- Compile all Python sources in the AI platform in memory.
- Run the AI entrypoint contract tests.
- Run the full AI platform suite, including the existing cost-control tests and new observability/fallback tests.
- Run the complete ACRL regression suite.
- Verify structured event fields do not include raw prompts, model outputs, credentials, or raw provider exceptions.
- Verify configured fallback selection, explicit model choice behavior, route output limits, and observability-failure handling.
- Verify no automatic retry after an ambiguous provider attempt.
- Complete T08 only through the existing Control Center `complete-subtask` command.
- Verify state integrity, the controller-created snapshot, packet and handoff markers, generated evidence, and canonical remote readback.
- Fail closed if any required test, state check, ownership check, or readback fails.

## Scope Restrictions

- This request authorizes AI-001-T08 only.
- AI-001-T09, T10 and all AI-001 gate acceptance criteria remain outside this request.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not create a duplicate gateway, observability port, or model registry.
- Do not introduce a new provider SDK or enable live provider credentials.
- Do not retry automatically after an ambiguous provider call.
- Do not enable production/customer-facing AI.
- Do not force-push or bypass the canonical Control Center.
- Do not claim completion unless the guarded transition and canonical readback pass.

## Final Authorization

The owner authorizes the guarded AI-001-T08 completion workflow to validate the exact commit containing this request. Completion is conditional on every required verification succeeding. The workflow must record actual evidence and preserve AI-001-AC01 through AI-001-AC06 as PENDING.
