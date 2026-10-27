# AI-001-T07 — Cost Controls and Usage Tracking Evidence

## Authority and exact verification

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Verified code commit: `56412641d2f7b7ecfc8bbba20728dbb6bf19d51c`
- GitHub Actions run: [40453851901](https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/40453851901)
- Completion route: existing Control Center `complete-subtask`
- Manual `state.json` editing: **not performed**
- Live provider credentials and production customer-facing AI: **not enabled**

## Test results on the verified commit

- AI entrypoint contract tests: **15 passed**
- AI platform cost controls and usage accounting tests: **151 passed**
- Complete ACRL regression suite: **1444 passed**
- AI package compilation: **PASS** (24 Python sources compiled in memory)
- Cost-control tests cover persistent SQLite readback, integer micro-USD pricing, tenant budget isolation, reservation-before-provider accounting, concurrent quota enforcement, idempotent settlement/release, request replay conflict, actual provider usage, conservative estimated charges when usage is unknown, over-budget recording, and UTC month boundaries.
- Accounting uses the existing `UsageControlPort` contract and existing gateway call path. Pricing and budgets are supplied by trusted server configuration; request callers cannot choose their own rates or tenant budget.

## Scope and integration boundary

`SQLiteUsageControl` is a persistent single-host reference adapter. Reservation/quota checks use SQLite transactions and a unique tenant/request/idempotency key boundary. Actual or conservative estimated charges are persisted in integer micro-USD, and costs above the reservation are recorded rather than discarded. Failed/ambiguous provider outcomes are not incorrectly released as zero-cost.

This implementation does **not** claim that SQLite on a shared network filesystem is a distributed quota ledger. Horizontally scaled production deployment must inject the same port backed by the approved shared transactional datastore. Provider prices, live service wiring, retention/operations policy, multi-replica deployment and live provider billing reconciliation remain deployment integration concerns. Live provider calls and customer-facing AI activation remain disabled. AI-001-AC01 through AI-001-AC06 remain PENDING; this subtask transition does not bulk-verify gate acceptance.

## Verified source blob SHAs

| File | Git blob SHA |
|---|---|
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/contracts.py` | `dad311757805055153c552825a8ecc054aa81347` |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/errors.py` | `ca9db169ca320b94ae28d2f6a0f779071712940a` |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/ports.py` | `1e745440484b77f455579288c93dc68b30ccfcf1` |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/model_gateway.py` | `fcc054d3980d30d0a61480b45d5ea624da43e61b` |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/cost_control.py` | `a34ea72d62f0edbaa9723a494548c90fdc0ae358` |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py` | `42a6b3787ad3e5f6b1b2218710e1c89fef5e7da6` |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_cost_control.py` | `deb0f1477d57de6afa5ea92a789c971be53c0475` |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py` | `83ab141f1d908fc208c4d67c470dedc154ec873d` |
| `.github/actions/homio-backend-ci/verification/scripts/compile_and_contracts.sh` | `c546b01685a850bf645b896e8b18a14f49e53b13` |
| `REOS_CONTROL_CENTER/tets/test_ai_agent_entrypoint_contract.py` | `a46a8393dfa3f33b4aada82b4fc5e2e953d1baed` |
| `REOS_CONTROL_CENTER/evidence/AI-001/T07-transition-request.md` | `0ccfc3e575c509551c12910269c755979cce9fbb` |

## Canonical state after controller transition

- State blob SHA before publishing this evidence: `1ceb2bea30ed938e920587c3a5c0719c61c37ff8`
- AI-001-T01 through AI-001-T07: `DONE`
- AI-001-T08: `CURRENT`
- AI-001-T09 through AI-001-T10: `PENDING`
- AI-001-AC01 through AI-001-AC06: `PENDING`

This record closes AI-001-T07 only. It does not claim the AI-001 gate or its acceptance criteria are complete, and it does not authorize production/customer-facing AI execution.
