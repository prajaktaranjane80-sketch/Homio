# HOMIO / REOS — Continue CORE-008 Backend Execution (T03 Transition Recovery → T04–T10)

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

### T03 — Commission allocation and participant split logic

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

## 3. Latest T03 transition attempt — actual result

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

T03 TRANSITION STOPPED — NO SUCCESS CLAIM
Guarded file changed during transition: REOS_CONTROL_CENTER/data/state.json
Guarded file changed during transition: REOS_CONTROL_CENTER/data/state.json
```

**Interpretation:** The local controller successfully produced output showing AC03 verified and T03 completed, with integrity and phase/gate coherence passing. However, the transition script subsequently aborted because it detected a change to `state.json`. It did not report successful completion of the atomic GitHub transition.

The printed hashes above are not proof that the corresponding state has been committed to GitHub.

### First task in this new chat

Perform a **targeted live readback**, not a broad re-audit:

1. Read the current `reos-development` HEAD.
2. Read the actual committed `REOS_CONTROL_CENTER/data/state.json`.
3. Read the latest `REOS_CONTROL_CENTER/PS Output`.
4. Check the relevant GitHub Actions run/commit evidence if available.

Then establish which of these is true:
- The T03 state transition was committed successfully by a later operation; or
- The code commit is present and passes CI, but the T03 state transition remains uncommitted.

Do not assume either outcome in advance.

If the transition is still pending, recover **only the T03 completion transition**. Do not rerun the implementation, claim success prematurely, or overwrite newer branch work.

The prior script's guard on `state.json` may have treated the controller's expected local state mutation as an unexpected change. Review that guard. Compare immutable source files against their expected hashes, validate the generated state and handoff separately, and atomically commit the canonical state, required handoff files and controller-generated snapshots. Use the live branch HEAD as the commit parent and abort safely if it changes during execution. Never force-push or make a partial state-only commit when the transition requires multiple artifacts.

Verify the transition by reading the committed files back from GitHub and checking its exact CI run. If verification cannot be completed, state precisely what remains unverified.

## 4. CORE-008 acceptance-criteria context

Previously observed state:
- AC02: VERIFIED.
- AC03: PENDING before the latest attempted transition; the local controller output subsequently reported `VERIFIED: CORE-008-AC03`.
- AC01, AC04, AC05 and AC06: PENDING before the latest attempted transition.
- CORE-008-T04 through T10: PENDING before the latest attempted transition.

Recheck the live state and use its current values as authoritative. Do not copy these historical statuses over newer committed state.

## 5. Remaining work after transition recovery

Continue CORE-008 from **T04 through T10**, in the exact sequence and with the exact task definitions in the canonical plan and current `state.json`.

### Immediate next subtask: CORE-008-T04

The reported description is:

**Implement settlement and reconciliation lifecycle.**

Inspect the relevant existing financial/commission modules, contracts, tests and task acceptance criteria. Follow the established architecture and repository conventions. Implement the actual lifecycle, including its required state transitions, validation and reconciliation safeguards, based on the canonical contracts—not guessed business rules.

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
