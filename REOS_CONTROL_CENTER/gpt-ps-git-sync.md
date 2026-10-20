# HOMIO / REOS - Canonical Task Continuity and Guarded GitHub Sync

> **CURRENT AUTHORITATIVE OVERLAY - 2026-10-20**
>
> - Always re-read the live `reos-development` HEAD and `REOS_CONTROL_CENTER/data/state.json` before acting.
> - The current canonical subtask is **CORE-008-T04**. T01-T03 are DONE; T04 is CURRENT; T05-T10 are PENDING.
> - The former T03 transition-recovery procedure below is historical context, **not** the current first action. Do not repeat T03 or run its old transition script.
> - Phase 0-1 reconciliation is recorded in `REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`.
> - The owner authorized Phase 0-1 reconciliation only. That does not change state.json, complete T04, or authorize unrelated runtime/state mutations.
> - Preserve verified T04 implementation. Validate pending acceptance criteria and existing evidence; only fix a demonstrated defect.
> - Do not infer a passing result on a newer SHA from a CI run on an older SHA.

## 1. Project and canonical references

**GitHub repository:**  
https://github.com/prajaktaranjane80-sketch/Homio

**Canonical branch:** `reos-development`

**Authoritative execution state:**  
`REOS_CONTROL_CENTER/data/state.json`

**Execution controller:**  
`REOS_CONTROL_CENTER/reos_control_center.py`

**Current diagnostic output:**  
`REOS_CONTROL_CENTER/PS Output`

**Canonical CORE-008 plan:**  
`REOS_CONTROL_CENTER/architecture/backend/plans/CORE-001 to CORE-008 Closure, Hardening & Architecture Integrity Active Plan`

Follow the repository's actual file and subtask definitions. Do not invent missing task names or assume a status that has not been verified.

## 2. Verified work already completed

### T01 and T02
- CORE-008-T01: DONE.
- CORE-008-T02: DONE.
- Previous T02 completion transition: `7cb3a6603c89d01531d8fb195a3d5769878ae474`.
- Prior acceptance-criterion evidence for AC02 and the corresponding test runs is documented in the preceding work context.

### T03 - Commission allocation and participant split logic

**Implementation commit:**  
`5adc036e7581345714d2d323a07beae5e4aea1ee`

Commit:  
https://github.com/prajaktaranjane80-sketch/Homio/commit/5adc036e7581345714d2d323a07beae5e4aea1ee

**T03 code CI passed:**
- GitHub Actions run: `39026668724`
- https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/39026668724
- Exact implementation SHA was verified against the run.
- Reported result: **502 passed in 1.35 seconds.**

Four implementation/test files were changed:
1. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/__init__.py`
2. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/commission_allocation.py`
3. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/commission_participant_split.py`
4. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/test_core008_t03_allocation_participants.py`

The implementation covers deterministic finite-precision ratio residue handling, allocation/state and entitlement guards, tenant and contract/version/currency consistency, and participant splitting tied to canonical Deal, lead attribution and ARCH-011 ownership references.

**Do not rewrite or repeat T03 implementation without evidence of a real defect.**

## 3. Latest T03 transition attempt - historical record only (NOT THE CURRENT ACTION)

The latest PowerShell output reported:

```text
STATE HASH STORED: 6f27f7589bdaf366017521b31fd12d82a3e96c625dbb1a1894b6428d781a68c6
STATE HASH CALCULATED: 6f27f7589bdaf366017521b31fd12d82a3e96c625dbb1a1894b6428d781a68c6
INTEGRITY: PASS
PHASE/GATE COHERENCE: PASS
VERIFIED: CORE-008-AC03
COMPLETED: CORE-008-T03
NEXT: CORE-008-T04: Implement settlement and reconciliation lifecycle.
STATE HASH STORED: 8df15eb0c98fa7b2a3bd6cea66e1e3c935ccf553e986537515a519d92a9c8173
STATE HASH CALCULATED: 8df15eb0c98fa7b2a3bd6cea66e1e3c935ccf553e986537515a519d92a9c8173
INTEGRITY: PASS
PHASE/GATE COHERENCE: PASS

T03 TRANSITION STOPPED - NO SUCCESS CLAIM
Guarded file changed during transition: REOS_CONTROL_CENTER/data/state.json
Guarded file changed during transition: REOS_CONTROL_CENTER/data/state.json
```

**Interpretation:** The local controller successfully produced output showing AC03 verified and T03 completed, with integrity and phase/gate coherence passing. However, the transition script subsequently aborted because it detected a change to `state.json`. It did not report successful completion of the atomic GitHub transition.

The printed hashes above are not proof that the corresponding state has been committed to GitHub.

### Current first action - follow canonical T04 state, not the historical T03 attempt

1. Read live `reos-development` HEAD, `data/state.json`, the current CORE-008 gate plan and T04 evidence.
2. Confirm T04 source/test blob SHAs and the corresponding CI run before changing implementation.
3. Use the canonical state for criterion status. AC01, AC04, AC05 and AC06 currently remain PENDING; AC02 and AC03 are VERIFIED.
4. Validate each pending criterion against existing implementation/tests. Do not repeat work without evidence of a defect.
5. Use the existing Control Center/controller workflow for any authorized state transition. Never edit `data/state.json` directly.
6. The owner-approved Phase 0-1 work updates supporting documents only. Later code changes must follow the active task or a separately authorized compliant scope.
7. If live branch/task differs from this snapshot, stop and follow fresh canonical evidence.

Do not use the historical T03 guard failure, old local state, or old HEAD values as current operational instructions.

## 4. Current CORE-008 acceptance-criteria context

The live canonical `data/state.json` read on 2026-10-20 reports:
- AC01 - Commission source of truth is authoritative: **PENDING**.
- AC02 - Deal and ownership attribution is traceable: **VERIFIED**.
- AC03 - Financial amounts use safe fixed-precision semantics: **VERIFIED**.
- AC04 - Settlement and reversal are auditable: **PENDING**.
- AC05 - Critical financial actions require appropriate approval: **PENDING**.
- AC06 - Security and concurrency tests pass: **PENDING**.

Current subtask: **CORE-008-T04**.

The T04 evidence record confirms these source/test blob SHAs matched the live branch:
- `commission_settlement_lifecycle.py`: `629e2388eeb40819923c943a5bb4ba2097ae2a2a`
- `commission_reconciliation.py`: `ffa7b4d0d392618b95d72360e0191988f9b3c167`
- `test_core008_t04_settlement_reconciliation_lifecycle.py`: `00e3bb5936d39eab155e4dbc119a587c92120019`
- `test_core008_t04_settlement_integrity_linkage.py`: `78e083609e78c298c924602f3e6a094a753be3a3`

Latest verified CI snapshot: [run 39429640103](https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/39429640103), commit `dfc967588dcbe4cb79793b53382042ec2ea2d36b`: 32 ACRL runtime-integration tests, 56 T07/T14 tests and 522 combined regressions passed. This evidence does not automatically verify every criterion or complete the T04 transition.

Re-read live state before relying on these values in a later session.

## 5. Remaining CORE-008 work - canonical sequence

Continue CORE-008 from **T04 through T10**, in the exact sequence and with the exact task definitions in the canonical plan and current `state.json`.

### Immediate next subtask: CORE-008-T04

The reported description is:

**Implement settlement and reconciliation lifecycle.**

Inspect the relevant existing financial/commission modules, contracts, tests and task acceptance criteria. Follow the established architecture and repository conventions. Implement the actual lifecycle, including its required state transitions, validation and reconciliation safeguards, based on the canonical contracts-not guessed business rules.

Write and run targeted regression tests. Run the required gate verification and available CI checks for the exact resulting commit. Do not update the authoritative state until the acceptance criteria and evidence satisfy the project's prescribed controller workflow.

### Then T05, T06, T07, T08, T09 and T10

Retrieve each subtask's real title, scope, dependencies, expected evidence and acceptance criteria from the canonical plan and repository. Work sequentially. Preserve dependencies and the distinction between:
- Implementation committed
- Tests passed
- Acceptance criterion verified
- Subtask formally completed in canonical state
- Entire CORE-008 gate approved and closed

T10 must not be treated as complete merely because earlier tests pass. Follow its actual approval and closure requirements.

## 6. Required working method

- **Do actual implementation work**, not another generic plan or endless audit.
- Inspect only the relevant files, live state, task contract and test evidence for the current subtask.
- Do not repeatedly audit already-passed T01/T02 or rerun unrelated frontend checks unless relevant changes require them.
- Preserve working T03 implementation and previous completed tasks.
- Use complete file replacements where necessary; avoid fragile anchor-based patches when a full replacement is safer.
- No isolated local worktree or Downloads-script workflow. Use the established authenticated PowerShell/GitHub process.
- Do not claim a remote commit exists until GitHub readback confirms it.
- Keep canonical state, generated next-chat packet, `REOS_NEXT_CHAT.txt` and required snapshots coherent when a formal subtask transition requires them.
- If a script fails, diagnose the exact failing guard and correct the root cause. Do not repeat the same failed block unchanged or execute orphaned `finally` sections separately.
- Treat `PS Output` as diagnostic evidence, not the source of truth.
- Do not modify unrelated frontend files or mix in the separate Imperium AI project.

## 7. Expected reporting after each subtask

Report briefly:
1. Exact subtask completed.
2. Actual changed repository paths.
3. Commit SHA and GitHub link.
4. Targeted test results and exact CI run.
5. Acceptance criterion status.
6. Canonical state transition and readback status.
7. Exact next subtask.

If any step is blocked, distinguish code/test success from formal state completion and specify the concrete blocker.

**Start now:** perform the targeted live GitHub readback for the T03 transition, recover it only if necessary, and then proceed with CORE-008-T04. Do not restart the project or redo working T03 code.

## 8. Phase 0-1 work-order reference

Master plan: `REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`.

Phase 0-1 is closed for the read-only baseline and documentation/authority reconciliation only. The canonical task remains T04. Audit-phase closure is not a business-subtask completion and does not permit direct state edits.