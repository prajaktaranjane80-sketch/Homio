
# AI-001-T03 Transition Request

APPROVAL: AUTHORIZE AI-001-T03 COMPLETION

SCOPE: AI-001-T03 only

## Verification Reference

- Latest successful baseline backend verification run: 40313769956 (Actions run #371)
- Verified baseline commit: b959231692b6e39a011cebccaa982a857c8a2b6e
- Baseline backend verification: PASS
- AI-001-T03 transition wiring verification: PASS
- Backend wiring tests: 30 passed
- Agent entrypoint contract tests: 15 passed
- AI platform tests, including embeddings and retrieval: 62 passed
- Complete ACRL regression suite: 1444 passed
- Pinned Qdrant dependency installation (`qdrant-client==1.20.0`): PASS

The baseline run verifies its recorded commit only. It does not authorize treating AI-001-T03 as completed without a new guarded run. The guarded transition must rerun the required checks against the exact triggering commit.

## Required Transition Checks

- Verify repository owner, canonical branch, actor and exact triggering commit SHA.
- Confirm that the current branch HEAD matches the exact triggering commit.
- Validate the canonical Control Center state before transition.
- Run the backend verification suite against the exact triggering commit.
- Run the canonical AI platform tests, including embeddings and retrieval.
- Run the agent entrypoint contract tests and complete ACRL regression suite.
- Confirm that the explicit authorization in this request remains valid.
- Complete AI-001-T03 only through the existing Control Center.
- Verify the resulting canonical state, packet, handoff, evidence, snapshot integrity and remote readback.
- Fail closed if any required validation or readback fails.

## Scope Restrictions

- This authorization applies only to AI-001-T03.
- AI-001-T04 and later subtasks are not approved by this request.
- AI-001-AC01 through AI-001-AC06 must remain PENDING.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not enable live providers or production vector services as part of this transition.
- Do not force-push or bypass the canonical Control Center.
- Do not claim completion unless the guarded transition and canonical readback both pass.
