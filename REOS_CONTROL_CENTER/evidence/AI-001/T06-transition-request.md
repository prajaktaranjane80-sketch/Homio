# AI-001-T06 Transition Request

APPROVAL: AUTHORIZE AI-001-T06 COMPLETION

SCOPE: AI-001-T06 only

## Verification Reference

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Task: Implement AI authorization and tenant isolation
- Required test: `test_authorization_tenant_isolation.py`
- Required integration regression: `test_agent_tool_boundaries.py`
- Required full regression: complete ACRL suite
- Completion route: existing Control Center `complete-subtask`

The guarded transition must verify the exact triggering commit. It must run the required AI entrypoint contract tests, the complete canonical AI platform test set, and the complete ACRL regression suite before requesting T06 completion.

## Required Transition Checks

- Verify repository owner, canonical branch, exact commit SHA, and commit-prefix authorization.
- Run Control Center `verify-state` before changing task status.
- Confirm T01–T05 are DONE and T06 is CURRENT.
- Compile the AI platform Python sources in memory.
- Test trusted-context validation, fail-closed dependency errors, invalid-operation rejection, resource authorization, tenant-isolation denial, and the ToolBridge boolean adapter.
- Run all canonical AI platform tests, including retrieval/RAG and agent-tool boundary tests.
- Run the complete ACRL regression suite.
- Call `complete-subtask AI-001-T06` through the existing Control Center only.
- Verify state integrity, controller-generated snapshot, packet/handoff markers, evidence, and canonical remote readback.

## Scope Restrictions

- This authorization applies only to AI-001-T06.
- AI-001-T07 through AI-001-T10 are not approved by this request.
- AI-001-AC01 through AI-001-AC06 must remain PENDING.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not create a second canonical identity, membership, or business-policy engine.
- Do not enable live provider credentials or production/customer-facing actions.
- Do not force-push or bypass the canonical Control Center.
- Do not claim completion unless the guarded transition and canonical readback pass.
