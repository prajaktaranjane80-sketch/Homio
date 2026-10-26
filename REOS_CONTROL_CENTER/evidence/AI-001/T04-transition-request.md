# AI-001-T04 Transition Request

APPROVAL: AUTHORIZE AI-001-T04 COMPLETION

SCOPE: AI-001-T04 only

## Verification Reference

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Baseline successful Actions run: 40319518149
- Baseline run number: #377
- Baseline verified code commit: `36d88d0fec6ba87ac87ebe27d2a623b8c374bccd`
- Baseline AI-focused tests: 89 passed
- Baseline AI entrypoint contract tests: 15 passed
- Baseline complete ACRL regression suite: 1444 passed
- RAG test: `test_retrieval_and_rag.py`
- Pinned retrieval dependency: `qdrant-client==1.20.0`

The successful baseline verifies its own commit only. It does not complete AI-001-T04. The guarded transition must execute verification again against the exact commit carrying this request and the required commit prefix.

## Required Transition Checks

- Verify repository owner, authorized actor, canonical branch and exact triggering commit SHA.
- Confirm that the canonical branch HEAD matches the exact triggering commit.
- Validate the canonical Control Center state before transition.
- Confirm T01, T02 and T03 are DONE and T04 is CURRENT before transition.
- Run AI entrypoint contract tests.
- Run all canonical AI platform tests, including embeddings/retrieval and prompt/RAG tests.
- Run the complete ACRL regression suite.
- Validate versioned prompt templates, untrusted retrieved-content handling, citation integrity, bounded context/output and safe behavior on missing evidence.
- Confirm this explicit authorization remains valid and restricted to T04.
- Complete AI-001-T04 only through the existing Control Center `complete-subtask` command.
- Verify canonical state integrity, controller snapshot integrity, packet/handoff markers, generated evidence and remote readback.
- Fail closed if any required validation or readback fails.

## Scope Restrictions

- This authorization applies only to AI-001-T04.
- AI-001-T05 and later subtasks are not approved by this request.
- AI-001-AC01 through AI-001-AC06 must remain PENDING.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not enable live providers or production vector services as part of this transition.
- Do not force-push or bypass the canonical Control Center.
- Do not claim completion unless the guarded transition and canonical readback both pass.
- Guarded completion trigger: owner-authorized AI-001-T04 transition after exact-commit verification.
