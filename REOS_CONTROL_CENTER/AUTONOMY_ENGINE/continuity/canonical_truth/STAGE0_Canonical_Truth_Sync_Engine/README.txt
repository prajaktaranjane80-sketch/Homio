STAGE 0 — CANONICAL TRUTH SYNC ENGINE
=====================================

Purpose
-------
This layer establishes the authoritative truth plane for HOMIO / REOS.
It prevents stale continuity packets, next-chat handoffs, and recovery artifacts
from becoming accidental sources of truth.

Authority hierarchy
-------------------
1. Frozen approved architecture
2. REOS_CONTROL_CENTER/data/state.json  <-- canonical execution state
3. Git repository                         <-- code/history truth
4. Generated continuity artifacts         <-- derived replicas only
5. Chat history                            <-- NEVER authoritative

Design goals
------------
- zero ambiguity about current execution state
- deterministic conflict detection
- fail-closed on critical state conflicts
- synchronize only derived artifacts
- never mutate canonical state directly
- preserve state fingerprint and Git revision
- make a fresh AI agent capable of discovering one coherent current position

What this layer writes
----------------------
- PROJECT_CONTINUITY/continuity_state.json
- REOS_NEXT_CHAT.txt
- artifacts/truth_sync/truth_manifest.json
- artifacts/truth_sync/sync_receipt.json

What this layer never writes
----------------------------
- data/state.json
- architecture approvals
- Git history
- deployment state
- human decisions

Integration
-----------
from STAGE0_Canonical_Truth_Sync_Engine import CanonicalTruthSyncController

controller = CanonicalTruthSyncController(Path("D:/HOMIO/REOS_CONTROL_CENTER"))
manifest, plan, receipt, report = controller.synchronize()

The canonical controller remains the only authority for state mutation.
