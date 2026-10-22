
# HOMIO / REOS — Canonical Task Continuity and Guarded GitHub Sync

> **CURRENT VERIFIED OVERLAY — 2026-10-22**
>
> - Canonical repository: `prajaktaranjane80-sketch/Homio`.
> - Canonical branch: `reos-development`.
> - Latest observed HEAD: `e716a1e3fe1bd5c12c7dd8d01ce935d7e0ad459b`.
> - Canonical state path: `REOS_CONTROL_CENTER/data/state.json`.
> - Canonical state blob SHA at this baseline:
>   `92296fb10b0c7a37d0fc7fa97c4328f587512150`.
> - Current canonical subtask remains **CORE-008-T04 — Implement settlement and reconciliation lifecycle**.
> - T01–T03 are complete. T04 remains current; T05–T10 remain pending unless changed by the canonical Control Center.
> - Phase 3 guarded synchronization foundations have targeted CI evidence on the latest observed commit. Do not interpret this as proof that all ACRL layers or all CORE-008 acceptance criteria are complete.
> - The owner has explicitly directed that Phase 4 workflow alignment begin. This authorizes only the bounded workflow-document, contract-test, CI and final EntryPoint alignment work described below; it does not authorize changing canonical execution state or modifying unrelated financial runtime code.
> - **Required implementation order:** reconcile supporting workflow documents → add and verify the EntryPoint contract test → wire the test into existing backend CI → update `AI_AGENT_ENTRYPOINT.py` last → independently verify the final commit and CI.
> - `AI_AGENT_ENTRYPOINT.py` must not be updated early or repeatedly while upstream workflow policy is still changing.
> - `state.json` remains canonical. This document, chat history and diagnostic outputs cannot authorize a state transition.
> - A CI result applies only to its exact tested commit SHA.
> - A file is not considered saved/verified until its committed content has been read back from GitHub.

## 1. Project and canonical references

**Repository:**  
https://github.com/prajaktaranjane80-sketch/Homio

**Canonical branch:** `reos-development`

**Canonical execution state:**  
`REOS_CONTROL_CENTER/data/state.json`

**Execution controller:**  
`REOS_CONTROL_CENTER/reos_control_center.py`

**Agent-facing workflow policy:**  
`REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py`

**Workflow instructions:**  
`REOS_CONTROL_CENTER/gpt-ps-git-sync.md`

**Master work order:**  
`REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`

**Platform-wide audit record:**  
`REOS_CONTROL_CENTER/architecture/HOMIO_ACRL_PLATFORM_WIDE_AUDIT_PLAN.json`

**Existing backend workflow:**  
`.github/workflows/backend-ci.yml`

**Existing contract-test folder:**  
`REOS_CONTROL_CENTER/tets/`

**Current CORE-008 plan:**  
`REOS_CONTROL_CENTER/architecture/backend/plans/CORE-001 to CORE-008 Closure, Hardening & Architecture Integrity Active Plan`

Do not invent task identifiers or assume a subtask status that has not been verified against live canonical state.

## 2. Latest verified repository and CI baseline

### Repository

- Repository: `prajaktaranjane80-sketch/Homio`
- Branch: `reos-development`
- Latest observed HEAD: `e716a1e3fe1bd5c12c7dd8d01ce935d7e0ad459b`
- HEAD commit:
  https://github.com/prajaktaranjane80-sketch/Homio/commit/e716a1e3fe1bd5c12c7dd8d01ce935d7e0ad459b
- Commit message: `Add component and new error handling details to contract`.
- `data/state.json` blob SHA:
  `92296fb10b0c7a37d0fc7fa97c4328f587512150`.
- EntryPoint blob observed before Phase 4:
  `2187ba939262863939beb0cadf8aa1b05af2117e`.
- This EntryPoint SHA is a baseline reference, not a claim that Phase 4 final alignment has been completed.

The exact existing root-level workflow path contains an en dash:

`HOMIO PowerShell–GitHub Workflow Plan`

Do not create a hyphen-named duplicate.

### Latest observed backend/ACRL CI

- Run: `39773259833` — Run #203.
- URL:
  https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/39773259833
- Tested SHA:
  `e716a1e3fe1bd5c12c7dd8d01ce935d7e0ad459b`
- Conclusion: `success`.

Targeted results in that run included:

- Runtime integration: 32 passed.
- T07/T14 resume and context: 64 passed.
- T18 authorization: 23 passed.
- T16/T17 source-impact analysis: 123 passed.
- T19 test selection: 16 passed.
- T20 patch verification: 57 passed.
- T21 Git coordination and API recovery: 139 passed.
- T22 checkpoint coordination: 21 passed.
- T23/T24 evidence and continuity: 66 passed.
- Canonical truth, authentication, finance, context and tenant suite: 451 passed.

These results support the targeted Phase 3 components. They are not evidence that every ACRL layer, the entire platform-wide audit or all CORE-008 acceptance criteria are complete.

### Canonical CORE-008 state

The current live state identifies:

- Current gate: `CORE-008`.
- Current subtask: `CORE-008-T04`.
- AC01 — Authoritative commission source of truth: `PENDING`.
- AC02 — Traceable deal and ownership attribution: `VERIFIED`.
- AC03 — Safe fixed-precision financial amounts: `VERIFIED`.
- AC04 — Auditable settlement and reversal: `PENDING`.
- AC05 — Appropriate approval for critical financial actions: `PENDING`.
- AC06 — Security and concurrency tests: `PENDING`.

Do not mark these criteria complete based on unrelated workflow tests. Do not transition or edit canonical state as part of Phase 4.

## 3. Authority and safety rules

1. GitHub `reos-development` is the canonical source for committed code and repository history.
2. `REOS_CONTROL_CENTER/data/state.json` is the canonical machine-readable execution and gate state.
3. The existing Control Center owns task selection, task acceptance and formal state transitions.
4. `AI_AGENT_ENTRYPOINT.py` is agent-facing workflow policy, not a second execution controller.
5. ACRL provides continuity, validation, authorization boundaries, Git coordination, evidence resolution and checkpoint handling. It must not become a second state authority or business-domain owner.
6. T18 governs execution authorization where applicable.
7. T20 governs repair/patch verification where applicable.
8. T21 governs Git repository read/write coordination.
9. T22 governs commit/checkpoint coordination where required.
10. T07 and T14 remain the existing bootstrap and repository-context mechanisms.
11. Chat history, old PowerShell output, generated handoffs and supporting plans are not canonical execution state.
12. Do not manually edit `data/state.json` to manufacture task completion or change the current task.
13. Do not bypass GitHub permissions, branch protection, repository rulesets, approvals or rate limits.
14. Do not create a second Git synchronization engine, checkpoint engine, evidence engine, continuity engine or state store.
15. Do not create a workflow runner named `HOMIO_REMOTE_WORKFLOW_SYNC.ps1` or use a competing standalone runner.
16. Never declare a remote write successful before independently verifying the exact branch, commit parent, changed paths and saved content.
17. Preserve existing passing functionality. Fix a demonstrated defect, not an assumed one.

## 4. Phase 4 scope and execution order

Phase 4 is the alignment of existing GPT instructions, GitHub workflow policy, contract tests and CI. The EntryPoint is the final consolidation step.

### Step 4.1 — Reconcile supporting workflow documents

Review and reconcile the following existing paths before updating the EntryPoint:

- `REOS_CONTROL_CENTER/gpt-ps-git-sync.md`
- `REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`
- `REOS_CONTROL_CENTER/architecture/HOMIO_ACRL_PLATFORM_WIDE_AUDIT_PLAN.json`
- `HOMIO PowerShell–GitHub Workflow Plan`
- `HOMIO_REOS_FIX_EXECUTION_STRUCTURE`

Required behavior:

- Remove stale instructions that conflict with live repository or canonical execution evidence.
- Keep historical error records as history; never turn them into current commands.
- Reconcile any conflicting statements about whether PowerShell, GitHub UI or local worktree operations are allowed.
- Preserve the exact canonical path and branch names.
- Distinguish supporting work plans from execution authority.
- Record the Phase 4 implementation order: supporting docs, contract tests, backend CI, EntryPoint last.
- Keep the current CORE-008-T04 task and its acceptance-criterion statuses unchanged.
- Do not mark Phase 4 complete merely because documents were saved.
- Do not modify unrelated frontend or financial-domain code under this scope.

Review existing content before making changes. Do not replace a correct document merely to normalize wording.

### Step 4.2 — Add the EntryPoint contract test

Target path:

`REOS_CONTROL_CENTER/tets/test_ai_agent_entrypoint_contract.py`

Before creating it, verify the exact path is absent on the live branch and confirm no equivalent existing test already covers the same contract.

The focused contract test must check:

- The canonical repository is `prajaktaranjane80-sketch/Homio`.
- The canonical branch is `reos-development`.
- `REOS_CONTROL_CENTER/data/state.json` remains the execution authority.
- Chat history, local output and supporting documents cannot change task authority.
- Local repository readiness is distinct from live GitHub branch-tip proof.
- A locally stored upstream-tracking ref is not represented as a fresh remote fetch or live GitHub verification.
- Dirty/untracked files, missing upstream configuration, local ahead/behind state and divergent local branches fail closed where required.
- The local EntryPoint preflight does not perform mutating Git operations.
- Remote content readback and commit-parent verification are separate evidence.
- T18 authorization, T20 patch verification, T21 Git coordination and T22 checkpoint coordination remain separate responsibilities.
- No duplicate synchronization runner, state store or ACRL authority is introduced.
- Test assertions match actual contract fields and behavior rather than relying only on comments or policy prose.

The test must be deterministic, network-independent and safe to run in CI.

### Step 4.3 — Integrate the test into the existing backend CI

Update the existing file only:

`.github/workflows/backend-ci.yml`

Required behavior:

- Preserve every existing test and compile check.
- Do not create a second backend workflow.
- Add a focused step for `tets/test_ai_agent_entrypoint_contract.py` after confirming that exact path exists.
- Preserve Python 3.12, current required dependencies and the current working-directory convention.
- Ensure a missing or misspelled test path cannot be silently ignored.
- Keep the workflow triggering for relevant EntryPoint, workflow, ACRL and test-file changes.
- Do not widen permissions beyond those required for read-only CI.
- The new CI run must test the commit containing the final EntryPoint changes.
- Preserve failed-run evidence and diagnose failures; do not delete checks to make CI green.

### Step 4.4 — Update `AI_AGENT_ENTRYPOINT.py` last

Do this only after the supporting workflow documents, contract tests and backend CI configuration are stable.

The final EntryPoint must accurately express the accepted contract:

- Canonical project, branch and state authority.
- The distinction between local repository preflight and live remote GitHub verification.
- Local dirty/untracked and ahead/behind diagnostics, with an explicit indication that a local upstream-tracking ref may be stale.
- No claim that local preflight proves the current remote tip or saved content.
- Clear separation of T18, T20, T21 and T22 responsibilities.
- Existing T07/T14 bootstrap and repository-context ownership.
- Exact path inspection, ADD/REPLACE/NO CHANGE classification and no-duplicate rules.
- No local worktree source writes.
- No competing synchronization runner or second source of truth.
- Truthful, independently verified reporting of commit, readback, tests and CI.
- Fail-closed behavior when authorization, branch identity, evidence or repository state is unclear.

Do not use the EntryPoint as a place to duplicate per-file implementation details, test transcripts or the entire project state. Detailed implementation belongs in the owning modules, contracts and evidence records.

The EntryPoint does not execute Git writes itself and must not override the canonical Control Center.

### Step 4.5 — Verify final alignment

After all approved changes are saved:

1. Read the live `reos-development` HEAD.
2. Read the exact committed content of every changed target.
3. Confirm the commit parent and changed-file list.
4. Verify `data/state.json` remains unchanged unless the existing authorized Control Center itself has made an independently verified transition.
5. Run the focused EntryPoint contract test and required backend regressions.
6. Confirm the Actions run tested the exact final commit.
7. Confirm all pre-existing required backend checks remain enabled.
8. Record any unresolved mismatch as `VERIFY` or `BLOCKED`.
9. Do not report Phase 4 as complete until those checks pass against the final relevant commit.

## 5. Required working method

For each authorized change:

1. Re-read the live branch HEAD and canonical state.
2. Read the exact target paths and blob SHAs on GitHub.
3. Inspect existing owners and tests before adding anything.
4. Classify each target as `ADD`, `UPDATE`, `VERIFY`, `NO CHANGE` or `BLOCKED`.
5. Preserve the existing correct implementation.
6. Use a complete file replacement when necessary; do not ask the owner to assemble an inferred patch.
7. Do not write project code through a local worktree.
8. Apply changes only through the owner-authorized GitHub editing workflow.
9. Read the saved file and resulting commit back from GitHub.
10. Run focused tests and applicable regressions.
11. Keep implementation, tests passed, criterion verified, formal task completion and phase completion as separate statuses.
12. Report exact evidence, including commit SHA and Actions URL, without guessing.

## 6. Current work boundary and handoff

The current canonical project subtask remains:

**CORE-008-T04 — Implement settlement and reconciliation lifecycle.**

Phase 4 workflow alignment is separately owner-requested and is bounded to the supporting workflow documents, contract test, existing backend CI configuration and final EntryPoint alignment described in Section 4.

This bounded work does not authorize:

- Direct changes to `data/state.json`.
- A manual CORE-008 task transition.
- Claiming that T04 is complete.
- Unrelated financial-runtime changes.
- A duplicate ACRL or Git workflow engine.
- Bypassing repository access or branch protection.

At the beginning and end of each implementation batch, record:

- Current live branch HEAD.
- Current canonical task and state blob SHA.
- Exact paths added or replaced.
- Commit SHA and URL, if a commit exists.
- Exact remote content readback result.
- Focused test result.
- Relevant Actions run URL and tested SHA.
- Any unresolved blocker.
- Next action in the owner-approved Phase 4 order.

The next action is the supporting-document reconciliation. The EntryPoint remains the final update and is not to be edited during the initial document batch.

END OF DOCUMENT
