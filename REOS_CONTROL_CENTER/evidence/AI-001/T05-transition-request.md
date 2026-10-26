# AI-001-T05 Transition Request

APPROVAL: AUTHORIZE AI-001-T05 COMPLETION

SCOPE: AI-001-T05 only

## Verification Reference

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Latest successful baseline run: 40328623546
- Baseline commit: `5a3e1154e906605a7ef09e3471501588558591ce`
- Baseline AI entrypoint contract tests: 15 passed
- Baseline AI platform, RAG and agent-tool tests: 114 passed
- Baseline complete ACRL suite: 1444 passed
- Agent runtime: `agent_runtime.py`
- Tool bridge: `tool_bridge.py`
- Focused test: `test_agent_tool_boundaries.py`

The baseline run verifies its own commit only. It does not complete AI-001-T05. The guarded transition must rerun the required verification against the exact commit carrying this authorization.

## Required Transition Checks

- Verify the authorized repository owner, canonical branch and exact triggering commit SHA.
- Confirm canonical branch HEAD matches the exact triggering commit.
- Run Control Center `verify-state` before transitioning.
- Confirm T01–T04 are DONE and T05 is CURRENT.
- Compile all AI package sources in memory.
- Run the AI entrypoint contract tests.
- Run all canonical AI platform tests, including retrieval/RAG and agent-tool boundary tests.
- Run the complete ACRL regression suite.
- Validate typed tool proposals, explicit allowlist, bounded iterations, duplicate-call detection, preflight/evidence denial and safe result redaction.
- Confirm this explicit authorization is restricted to T05.
- Complete T05 only through the existing Control Center `complete-subtask` command.
- Verify the generated snapshot, state integrity, packet/handoff markers, evidence and canonical remote readback.
- Fail closed if any required verification fails.

## Scope Restrictions

- This authorization applies only to AI-001-T05.
- T06 and subsequent subtasks are not approved by this request.
- AI-001-AC01 through AI-001-AC06 must remain PENDING.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not add unrestricted shell, database or repository access.
- Do not enable sensitive business mutations or production/customer-facing agent execution.
- Do not force-push or bypass the canonical Control Center.
- Do not claim completion unless the guarded transition and canonical readback pass.
- Final activation: owner requests guarded AI-001-T05 completion on the exact verified commit.
