# BACKEND-001-B3 — Owner Completion Request

**Project:** HOMIO / REOS  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`

## 1. Explicit owner authorization

APPROVAL: AUTHORIZE BACKEND-001-B3 COMPLETION

SCOPE: BACKEND-001-B3 only

This approval authorizes only the guarded completion of the existing Python domain-runtime bridge foundation after exact-commit backend/ACRL verification, the B3-specific regression tests, and the T15/T17/T18 owner-authorized transition all pass.

This approval does not authorize B4, B2 production binding, customer-route activation, the full backend gate, or production release.

B3 remains a private, authenticated, read-only IPC foundation.

Mutation operations remain disabled until B4 supplies the durable idempotency and transaction owner.

BACKEND-001-AC01 through BACKEND-001-AC10 remain PENDING.

Manual `state.json` editing is prohibited.

## 2. Exact source baseline

The guarded transition is pinned to the audited live source baseline:

- Repository HEAD: `b0d6b8c2cf0d9e5c32c719d20915fe1d24e2fd3c`
- Canonical `state.json` blob SHA: `19a40749611c98bab182b9853ed6a25c986d2eb8`
- `HOMIO_Backend_Structure` blob SHA: `f8d9cd456568cc6c8eaae0caf764123a7e859ba6`
- B3 versioned contract blob SHA: `76b24db805c8105a85b5c141037485f01d19c757`

The guard independently checks that the baseline is an ancestor, that the canonical state and master plan remain unchanged in the owner source commit, that the existing B3 owner files retain their audited blob SHAs, and that the changed source path set matches the exact reviewed allowlist.

## 3. B3 is the read-only private runtime foundation

B3 closes the existing Node-managed child-process JSON Lines IPC foundation only. The approved single runtime owner remains:

- TypeScript transport client: `REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/client.ts`
- TypeScript contract: `REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/contracts.ts`
- Python protocol: `REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/protocol.py`
- Python worker: `REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/worker.py`
- Versioned contract: `REOS_CONTROL_CENTER/backend/contracts/python-runtime/v1/contract.json`

The existing boundary provides authenticated service-to-service IPC, versioned request/response envelopes, bounded serialization and message sizes, trusted actor/tenant/correlation propagation, replay protection, worker lifecycle and bounded concurrency, timeout/cancellation, and safe failure classification. Python domain rules remain in their existing Python owners; TypeScript contains transport validation and adaptation only.

B3 remains private. It introduces no public Python HTTP listener, no second public API, and no ACRL dependency in the customer runtime.

## 4. Durable mutation safety remains a B4 prerequisite

B3 remains an `ACTIVE_READ_ONLY_FOUNDATION`:

- The allowlisted operations remain the four existing OIDC/CORE-001 read operations.
- Mutation operations remain disabled.
- A non-null idempotency envelope is rejected with `MUTATION_NOT_ENABLED`.
- Automatic mutation retries remain disabled.
- No in-memory, process-local, or mock idempotency store may be used as a production substitute.
- Mutation enablement is prohibited until B4 supplies the canonical durable idempotency identity, tenant/operation binding, payload fingerprint, durable outcome reconciliation, same-key/different-payload conflict handling, and crash-after-commit-before-response recovery evidence.

This boundary is intentional: B3 cannot produce an ambiguous mutation outcome because it does not admit mutation operations. B4 remains the next authorized subtask and supplies the durable owner before later production binding.

## 5. Exact B3 acceptance scope

The guarded completion verifies these current B3 criteria without changing their wording:

1. Private TypeScript-to-Python runtime transport is authenticated.
2. Request and response contracts are versioned and validated.
3. Trusted actor, tenant and correlation context are preserved.
4. Timeout, cancellation and failure classification are tested.
5. Ambiguous mutation outcomes use durable idempotency identity. B3 satisfies this boundary by rejecting all mutation operations and non-null idempotency until B4 supplies the durable idempotency owner; no mutation outcome is retried or treated as committed by this B3 foundation.
6. No Python business logic is copied into TypeScript.
7. No second public Python API is exposed.

The backend CI verification job must pass on the exact triggering SHA, including Python runtime tests, TypeScript integration tests, reproducible build, and the complete ACRL suite. The dedicated B3 tests additionally prove unknown mutation operations fail before any domain owner is invoked and missing production owner composition fails closed without leaking module or exception details.

## 6. Guarded owner and architecture authorization

The transition must reuse the existing Control Center and ACRL authorization owners:

- T15 produces a bounded proposal; it never executes or mutates state.
- T17 analyzes the exact source paths; unknown or protected impacts block the transition.
- T18 authorizes only the exact B3 scope using the signed GitHub Actions workload identity of the immutable repository owner.
- The existing `REOS_CONTROL_CENTER/reos_control_center.py` `complete-subtask BACKEND-001-B3` command owns the state transition.
- The OIDC bearer token is ephemeral and must never be written to state, evidence, logs, artifacts, or Git.

The guarded job must stop if the owner, repository, branch, push event, source SHA, baseline state, master plan, contract, changed paths, current subtask, acceptance criteria, or T15/T17/T18 decision differs from this request.

## 7. Exact permitted transition

Use the existing Control Center command through the dedicated guarded B3 action:

`complete-subtask BACKEND-001-B3`

The guarded transition must:

1. Verify the exact owner push, repository, branch and triggering SHA.
2. Verify the exact baseline state, master plan, contract and unchanged existing B3 source owners.
3. Verify the exact approved source-path allowlist and this owner request.
4. Validate the read-only B3 contract and durable B4 mutation prerequisites.
5. Obtain GitHub OIDC identity and validate immutable owner/repository/branch/SHA claims with the existing OIDC verifier.
6. Run T15 proposal, T17 exact-path impact analysis and T18 explicit owner authorization.
7. Validate canonical pre-transition state and current B3 acceptance criteria.
8. Execute the existing Control Center `complete-subtask BACKEND-001-B3` command.
9. Validate canonical post-transition state, snapshot integrity, handoff markers and B4 current projection.
10. Record sanitized evidence without any bearer token.
11. Commit and push only the Control Center state, handoff, snapshot and B3 evidence outputs from the guarded GitHub Actions executor.
12. Verify remote branch SHA, remote state blob SHA, remote evidence, and handoff readback.

No manual `state.json` editing is authorized. The assistant and the owner do not write to GitHub through this request; the user saves the source files and pushes the owner-authorized commit.

## 8. Exact trigger

The owner-authorized source commit must be a non-empty commit on `reos-development` whose subject starts with:

`[CONTROL-CENTER-COMPLETE-BACKEND-001-B3]`

The existing backend verification job must pass first. Only then may the dedicated B3 guarded job run.

## 9. Expected canonical state after successful completion

- BACKEND-001-B0: `DONE`
- BACKEND-001-B1: `DONE`
- BACKEND-001-B2-FOUNDATION: `DONE`
- BACKEND-001-B3: `DONE`
- BACKEND-001-B4: `CURRENT`
- BACKEND-001-B2-PRODUCTION-BINDING: `PENDING`
- BACKEND-001-B5 through B10: `PENDING`
- BACKEND-001-AC01 through BACKEND-001-AC10: `PENDING`

The canonical technical sequence remains:

`B0 -> B1 -> B2-FOUNDATION -> B3 -> B4 -> B2-PRODUCTION-BINDING -> B5 -> B6 -> B7 -> B8 -> B9 -> B10`

## 10. Explicit exclusions

This approval does not authorize:

- Implementing B4 PostgreSQL persistence or durable idempotency in B3.
- Enabling Python mutation operations or automatic mutation retries.
- Constructing in-memory production identity, tenant, membership, session, audit, or idempotency stores.
- Creating a second runtime bridge, worker, owner registry, or public Python API.
- Enabling protected customer routes or production security adapters.
- Editing `state.json` manually or bypassing the Control Center.
- Verifying or bulk-changing BACKEND-001-AC01 through AC10.
- Completing B4, B2 production binding, or the whole backend gate.
- Claiming production readiness or production release approval.
- Changing frontend files, UI, CSS, or design systems.

The guarded transition must stop on any baseline drift, unexpected source path, unverified impact, failed verification, missing owner authorization, state mismatch, or failed remote readback.
