# AI-001 Acceptance Validation Request

APPROVAL: AUTHORIZE AI-001 ACCEPTANCE VALIDATION

SCOPE: AI-001-AC01 through AI-001-AC06 only

## Validation objective

Validate the six AI-001 acceptance criteria on the exact verified source commit using the existing AI platform and the existing CORE-005 search/indexing owner. Reuse the current gateway, authorization, model registry, tool bridge, cost controls, observability, retrieval, Qdrant indexing, projection sync and rebuild-adapter boundaries.

Do not introduce another gateway, indexer, registry, authorization engine, agent runtime, tool engine, or duplicate test tree.

## Required verification

- Verify the repository owner, `reos-development` branch, triggering commit SHA and guarded commit-prefix authorization.
- Run the canonical Control Center `verify-state` command and validate the canonical state integrity before any task-state transition.
- Confirm AI-001 is `READY_FOR_VALIDATION`, T01–T09 are `DONE`, T10 is `PENDING`, and AC01–AC06 are all `PENDING`.
- Run focused tests for each acceptance criterion.
- Run the complete AI platform regression suite; require at least 157 passing tests.
- Run the entrypoint contract suite; require at least 15 passing tests.
- Run the complete ACRL regression suite; require at least 1444 passing tests.
- Compile existing AI and indexing/retrieval Python source modules in memory.
- For AC03, verify existing source provenance, tenant isolation, stale-version protection, deterministic point identity, version-aware upsert behavior, and the canonical rebuild handoff. Do not claim a production-wide physical rebuild unless that behavior is directly tested.
- Verify each criterion separately through the existing Control Center `verify-criterion` command.
- Run the Control Center `validate-gate` command only after all six criteria have verified evidence.
- Verify every controller-created snapshot, packet/handoff marker, canonical state integrity digest, evidence record and remote branch readback.
- Fail closed on a test failure, insufficient test count, source inventory drift, duplicate test path, unexpected state transition, missing snapshot, integrity error or remote readback mismatch.

## Scope restrictions

- This request authorizes validation of AI-001-AC01 through AI-001-AC06 only.
- Do not execute `approve-gate`.
- Do not mark AI-001-T10 complete, approved or frozen.
- Do not edit `REOS_CONTROL_CENTER/data/state.json` manually.
- Do not enable live provider credentials, production tool execution or customer-facing AI.
- Do not create duplicate implementation modules or test trees.
- Do not claim success before the exact-commit tests and canonical remote readback pass.

## Conditional completion

The validation transition may complete only if all focused and full regression suites pass, each criterion receives its own evidence through the existing Control Center, the existing Control Center validates the gate, and remote readback confirms the resulting state.

AI-001-T10 approval and freeze are NOT authorized by this request
