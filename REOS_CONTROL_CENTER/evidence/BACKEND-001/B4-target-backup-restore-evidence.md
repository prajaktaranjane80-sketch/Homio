# HOMIO / REOS — B4 Target Backup and Restore Evidence

**Document ID:** B4-TBRE-001  
**Workstream:** BACKEND-001  
**Subtask:** BACKEND-001-B4 — PostgreSQL integration  
**Architecture:** ARCH-037 — Database Final Schema Design v1.0  
**Evidence status:** `CI_RECOVERY_VERIFIED_TARGET_ENVIRONMENT_PENDING`  
**B4 completion status:** `NOT_COMPLETE`

---

## 1. Evidence identity

| Field | Verified value |
|---|---|
| Repository | `prajaktaranjane80-sketch/Homio` |
| Branch | `reos-development` |
| Tested source commit | `afbaa1910696a9def96f1c7b1f79e8eaa9b78106` |
| Commit message | `Update postgres-b4-recovery.integration.test.ts` |
| Recovery test path | `REOS_CONTROL_CENTER/backend/tests/integration/postgres-b4-recovery.integration.test.ts` |
| Recovery test blob SHA | `bfbb50bcf0fcda8f857a6c63a4006ef98e28c322` |
| `state.json` blob SHA | `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b` |
| B4 work-plan blob SHA | `84c94c82ac5b0fde7c7bdf94acca235402c465ab` |
| Backend master blob SHA | `f8d9cd456568cc6c8eaae0caf764123a7e859ba6` |
| CI workflow | `HOMIO Backend and ACRL Runtime CI` |
| Workflow run | `45627180980` |
| Run number / attempt | `1044 / 1` |
| Verification job | `139250369889` |
| Run URL | https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/45627180980 |

---

## 2. Recovery method

**Verified method:** Full PostgreSQL logical database dump restored into a separately created database.
**CI machine method marker:** `FULL_DATABASE_PG_DUMP_TO_SEPARATE_DATABASE`

The recovery test now uses the complete canonical migration manifest. It does not restrict the backup to `reos_infra`.

| Property | Result |
|---|---|
| Source database | `homio_b4_recovery_cc49fdbf8fc6c828` |
| Restore database | `homio_b4_restore_cc49fdbf8fc6c828` |
| Source and target | Separate databases |
| PostgreSQL version | `18.4` |
| Backup method | Full `pg_dump` SQL snapshot |
| Backup SHA-256 | `68de1f72696eb3e95565d7aa3b9b3da7e9c4f81cf22f5bfa25e5ce94257732b2` |
| Backup size | `113631` bytes |
| Schema fingerprint SHA-256 | `361ba457101a2f7db02bce83acbfbe351b809c5bc4ff47c383d256a4b1ea575c` |
| Canonical migrations | `11` |
| Migration replay after restore | `0` newly applied |
| Recovery verification | `PASS` |

The restore target was a newly created database in the same temporary GitHub Actions PostgreSQL service/container. It was not an independently hosted database server or cluster.

---

## 3. Restored schema and data verification

The test verifies these managed schemas:

- `core001`
- `core002`
- `core003`
- `core004`
- `core006`
- `core007`
- `core008`
- `reos_infra`

Restored database assertions:

| Restored object | Expected / verified count |
|---|---:|
| Migration ledger rows | 11 |
| Tenants | 2 |
| Leads | 2 |
| API sessions | 3 |
| Security audit records | 1 |

The restored migration ledger is checked against the complete current migration manifest. Migration IDs and checksums must match. The post-restore migration runner applies zero new migrations.

---

## 4. Security verification after restore

| Control | Result |
|---|---|
| Database CONNECT ACL | `PASS` |
| PUBLIC database CONNECT removed | `PASS` |
| Migration and application roles separated | `PASS` |
| Application runtime role safety | `PASS` |
| Schema and table ownership | `PASS` |
| Tenant-bearing table RLS enabled | `PASS` |
| Tenant-bearing table FORCE RLS enabled | `PASS` |
| Tenant ownership after restore | `PASS` |
| Cross-tenant isolation after restore | `PASS` |
| Session and revocation records restored | `PASS` |
| Audit record and append-only protections | `PASS` |
| Application-role privilege boundaries | `PASS` |

CI log markers:

```text
B4_RECOVERY_SCHEMA_INTEGRITY=PASS
B4_RECOVERY_DATA_INTEGRITY=PASS
B4_RECOVERY_TENANT_ISOLATION=PASS
B4_RECOVERY_DATABASE_ACL=PASS
B4_RECOVERY_ROLE_AND_GRANT_INTEGRITY=PASS
B4_RECOVERY_VERIFICATION=PASS
```

---

## 5. Exact recovery test result

Test:

`tests/integration/postgres-b4-recovery.integration.test.ts`

Test case:

`restores actual B4 migrations, active and revoked sessions, audit records and security boundaries`

Result:

- 1 recovery integration test passed.
- Runtime reported by Vitest: approximately 1.318 seconds.
- Full backend Vitest run: 24 test files passed, 201 tests passed.
- The exact source SHA was checked out by the workflow before execution.

---

## 6. Recovery target classification

The run explicitly emitted:

```text
B4_RECOVERY_TARGET_CLASS=EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4
B4_RECOVERY_PRODUCTION_TARGET=NOT_TESTED
```

This evidence proves automated disposable CI recovery only.

It does not prove a controlled non-production target restore or a production disaster-recovery exercise.

---

## 7. Target controls not yet verified

The following requirements from B4 Work Plan §32 remain unverified by this CI run:

| Required target control | Status |
|---|---|
| Backup encryption at rest | `NOT_TESTED` |
| Secure backup transport | `NOT_TESTED` |
| Production backup access control | `NOT_TESTED` |
| Retention metadata and retention enforcement | `NOT_TESTED` |
| Backup access audit | `NOT_TESTED` |
| Key management and key rotation | `NOT_TESTED` |
| Restricted restore operator | `NOT_TESTED` |
| Target-environment restore runbook | `NOT_TESTED` |
| Independent controlled non-production restore | `NOT_TESTED` |
| Production disaster-recovery exercise | `NOT_TESTED` |
| WAL archive configuration and availability | `NOT_TESTED` |
| Base backup and recovery-target selection | `NOT_TESTED` |
| Point-in-time recovery (PITR) | `NOT_TESTED` |
| Post-PITR tenant and schema verification | `NOT_TESTED` |

A logical `pg_dump` snapshot is not a PITR test.

The run did not publish a durable B4 backup archive. The backup identity, size and digest were emitted in the workflow logs. The run's uploaded artifacts were the ACRL resume cache and Section 14 quality evaluation; neither is a B4 backup artifact.

No database passwords or other secret values are recorded in this evidence document.

---

## 8. Evidence sources

1. Exact recovery integration test:  
   https://github.com/prajaktaranjane80-sketch/Homio/blob/reos-development/REOS_CONTROL_CENTER/backend/tests/integration/postgres-b4-recovery.integration.test.ts

2. Exact GitHub Actions run:  
   https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/45627180980

3. B4 execution contract, §32 and §47–48:  
   https://github.com/prajaktaranjane80-sketch/Homio/blob/reos-development/REOS_CONTROL_CENTER/B4%20ka%20work%20plan

4. Authoritative task state:  
   https://github.com/prajaktaranjane80-sketch/Homio/blob/reos-development/REOS_CONTROL_CENTER/data/state.json

---

## 9. Final classification

**Automated full-database backup and separate-database restore:** `VERIFIED_PASS`

**Controlled target-environment recovery:** `NOT_VERIFIED`

**Production disaster recovery:** `NOT_TESTED`

**Point-in-time recovery:** `NOT_TESTED`

**B4 Phase 8:** `CI_RECOVERY_PROOF_AVAILABLE_TARGET_CONTROLS_PENDING`

**B4 subtask:** Remains `CURRENT`.

This evidence must not be used to mark B4 DONE. The remaining target controls, the complete B4 acceptance criteria, B4-specific guarded workflow, owner authorization, guarded Control Center transition and independent remote `state.json` readback must still be satisfied.
