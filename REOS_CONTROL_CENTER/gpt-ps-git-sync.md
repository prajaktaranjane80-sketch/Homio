# HOMIO / REOS — Canonical Task Continuity and Guarded GitHub Sync

> **CURRENT VERIFIED OVERLAY — 2026-10-21**
>
> - Always re-read live `reos-development` HEAD and
>   `REOS_CONTROL_CENTER/data/state.json` before acting.
> - Current canonical subtask: **CORE-008-T04**. T01–T03 are DONE;
>   T04 is CURRENT; T05–T10 are PENDING.
> - The T03 transition-recovery transcript below is historical evidence.
>   Do not repeat T03 or run its old transition script.
> - The master work order is
>   `REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`.
> - `state.json` remains canonical. This document and chat history never
>   authorize a state transition.
> - Phase 0 is the read-only baseline and path inventory. Phase 1 reconciles
>   the active task and authorized route. A saved document is not verified
>   until its exact committed content is read back from GitHub.
> - The owner authorized Phase 0–1 and workflow-document reconciliation.
>   This is not authorization to mark T04 complete or to make unrelated
>   runtime changes.
> - Preserve working T04 implementation. Fix only a demonstrated defect.
> - A CI success applies to its exact tested SHA, not automatically to HEAD.

## 1. Project and canonical references

**Repository:**  
https://github.com/prajaktaranjane80-sketch/Homio

**Canonical branch:** `reos-development`

**Authoritative execution state:**  
`REOS_CONTROL_CENTER/data/state.json`

**Execution controller:**  
`REOS_CONTROL_CENTER/reos_control_center.py`

**Diagnostic output:**  
`REOS_CONTROL_CENTER/PS Output`

**Master work order:**  
`REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`

**Platform-wide audit record:**  
`REOS_CONTROL_CENTER/architecture/HOMIO_ACRL_PLATFORM_WIDE_AUDIT_PLAN.json`

**CORE-008 active plan:**  
`REOS_CONTROL_CENTER/architecture/backend/plans/CORE-001 to CORE-008 Closure, Hardening & Architecture Integrity Active Plan`

Follow the repository's actual file and subtask definitions. Do not invent
missing task names or assume a status that has not been verified.

## 2. Verified work already completed

### T01 and T02

- CORE-008-T01: DONE.
- CORE-008-T02: DONE.
- Previous T02 completion transition:
  `7cb3a6603c89d01531d8fb195a3d5769878ae474`.
- Preserve prior criterion evidence and passing implementation.

### T03 — Commission allocation and participant split logic

Implementation commit:

`5adc036e7581345714d2d323a07beae5e4aea1ee`

Commit URL:

https://github.com/prajaktaranjane80-sketch/Homio/commit/5adc036e7581345714d2d323a07beae5e4aea1ee

Recorded T03 CI run:

- Run `39026668724`
- https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/39026668724
- Reported result: 502 passed.

The implementation/test files were:

1. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/__init__.py`
2. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/commission_allocation.py`
3. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/commission_participant_split.py`
4. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/test_core008_t03_allocation_participants.py`

Do not rewrite or repeat T03 implementation without evidence of a real defect.

## 3. Historical T03 transition attempt — NOT THE CURRENT ACTION

The historical PowerShell output included:

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

Interpretation:

- The transcript records that the local controller output reported AC03
  verified and T03 completed.
- The transition script subsequently aborted after detecting a state-file
  change.
- Those printed hashes do not prove a corresponding state was committed
  to GitHub.
- This is a historical error record, not a current instruction to recover
  T03 or to run the old transition script.

The canonical state now identifies T04 as CURRENT. Follow that live state.

## 4. Fresh live baseline — 2026-10-21

### Repository and state

- Live HEAD:
  `b917d5036ff5d9a3dea78a27ae9439cf8357f5fd`
- HEAD commit:
  https://github.com/prajaktaranjane80-sketch/Homio/commit/b917d5036ff5d9a3dea78a27ae9439cf8357f5fd
- The HEAD commit renames `REOS_CONTROL_CENTER/Frontend Ps Output` to
  `REOS_CONTROL_CENTER/Chat histry`; it does not change T04 implementation.
- Canonical state blob:
  `92296fb10b0c7a37d0fc7fa97c4328f587512150`
- Current gate: `CORE-008`
- Current subtask: `CORE-008-T04`.

The exact original root-level workflow-plan path contains an en dash:
`HOMIO PowerShell–GitHub Workflow Plan`.
Do not create a hyphen-named duplicate.

### Latest observed backend CI evidence

- Workflow run: `39600469687`
- URL:
  https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/39600469687
- Tested SHA:
  `9a6a6065ca4848b6b419a32e5bb1de5d3ab42246`
- Result: SUCCESS.

This run is on the parent code commit, not on HEAD
`b917d5036ff5d9a3dea78a27ae9439cf8357f5fd`. No backend CI run on that
exact diagnostic-rename HEAD was observed. Do not claim otherwise.

### Current T04 files verified against live blobs

- `commission_settlement_lifecycle.py`:
  `629e2388eeb40819923c943a5bb4ba2097ae2a2a`
- `commission_reconciliation.py`:
  `ffa7b4d0d392618b95d72360e0191988f9b3c167`
- `test_core008_t04_settlement_reconciliation_lifecycle.py`:
  `00e3bb5936d39eab155e4dbc119a587c92120019`
- `test_core008_t04_settlement_integrity_linkage.py`:
  `78e083609e78c298c924602f3e6a094a753be3a3`
- `commission_reconciliation_history.py`:
  `a5f8dad906c175a33a034e059a1fcc9c419e0fac`
- `test_core008_t04_reconciliation_replay.py`:
  `32626d845518a6b9da660f376e96112281adb36e`

These hashes identify the current read-back versions. Re-read them again
before any future code write.

## 5. Current CORE-008 acceptance criteria

The current task/evidence record reports:

- AC01 — Commission source of truth is authoritative: **PENDING**.
- AC02 — Deal and ownership attribution is traceable: **VERIFIED**.
- AC03 — Financial amounts use safe fixed-precision semantics: **VERIFIED**.
- AC04 — Settlement and reversal are auditable: **PENDING**.
- AC05 — Critical financial actions require appropriate approval: **PENDING**.
- AC06 — Security and concurrency tests pass: **PENDING**.

The earlier CI run `39429640103` on SHA
`dfc967588dcbe4cb79793b53382042ec2ea2d36b` reported 32 runtime-integration
tests, 56 T07/T14 tests and 522 combined regressions passed. This is
historical evidence for that exact SHA only.

Do not infer that all T04 criteria are verified from either a general CI
success or a later file's existence.

## 6. Immediate work after document synchronization

The next business subtask remains:

**CORE-008-T04 — Implement settlement and reconciliation lifecycle.**

Once the Phase 0–1 document corrections have been saved and independently
read back:

1. Read live `reos-development` HEAD and canonical state again.
2. Re-read the CORE-008 plan, T04 evidence and target blobs.
3. Validate AC01, AC04, AC05 and AC06 against criterion-specific evidence.
4. Preserve existing implementation unless a concrete defect is proven.
5. Inspect existing tests before proposing any new test or module.
6. Implement only a correction within the authorized T04 scope.
7. Run focused regressions and the configured backend workflow for the
   exact changed code commit.
8. Use the existing Control Center/controller route for any formal state
   transition. Never edit `state.json` directly.

Reversal-specific rules belong to T05. Do not implement a separate reversal
engine in T04 without an explicit dependency decision and authorization.

## 7. Remaining task order

Follow the live canonical plan in order:

- CORE-008-T04 — settlement and reconciliation lifecycle: CURRENT.
- CORE-008-T05 — dispute and reversal rules: PENDING.
- CORE-008-T06 — financial audit and evidence: PENDING.
- CORE-008-T07 — financial reporting hooks: PENDING.
- CORE-008-T08 — precision and concurrency tests: PENDING.
- CORE-008-T09 — financial security and approval review: PENDING.
- CORE-008-T10 — freeze commission and financial core: PENDING.

Retrieve each subtask's real title, dependencies, task contract and
acceptance criteria from canonical sources. Do not invent or reorder tasks.

Keep these states distinct:

- Implementation committed
- Tests passed
- Acceptance criterion verified
- Subtask formally completed in canonical state
- Entire CORE-008 gate approved and closed

## 8. Required working method

- Do actual authorized implementation work, not another generic plan.
- Inspect the relevant live state, files, task contract and test evidence.
- Do not repeatedly audit completed T01–T03 or rerun unrelated frontend
  verification when the current change does not require it.
- Preserve working code and existing passing tests.
- Use full file replacements when necessary; avoid fragile anchor-based
  patches when a whole-file replacement is safer.
- Use the owner's selected GitHub editing workflow. Do not create a
  Downloads-script or isolated local-worktree workflow.
- Do not claim a remote commit exists until GitHub read-back confirms it.
- Do not use `PS Output` or chat history as execution authority.
- Do not modify unrelated frontend files or mix in Imperium AI.
- If a script fails, diagnose the exact guard. Do not repeat the same failed
  block unchanged or run orphaned success/finally steps independently.

## 9. Phase 0–1 work-order reference

Master work order:

`REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`

Phase 0 covers the fresh read-only baseline, path inventory and duplicate/
equivalence checks. Phase 1 reconciles the active canonical task, authorized
scope and supporting instructions.

The active task remains T04. The Phase 0–1 document work never changes
`state.json`, never completes T04 and never authorizes unrelated runtime
changes.

After any document save, independently verify the exact committed paths,
contents, resulting HEAD, changed-file list and unchanged canonical state
before reporting document synchronization as successful.

The next action is to finish that remote read-back, then resume T04 from
canonical state—not to repeat the old T03 transition attempt.

END OF PLAN
