# HOMIO / REOS — B4 Completion CI Evidence

**Document ID:** B4-CI-001
**Workstream:** BACKEND-001
**Subtask:** BACKEND-001-B4 — PostgreSQL integration
**Architecture:** ARCH-037 — Database Final Schema Design v1.0
**Evidence status:** `GUARDED_B4_COMPLETION_VERIFIED`
**Production release readiness:** `NOT_CLAIMED`

## 1. Exact source and authority identity

- Repository: `prajaktaranjane80-sketch/Homio`
- Branch: `reos-development`
- Exact source SHA: `17784ada3e96edc5182cebb9cc548b2266b40296`
- `state.json` baseline blob SHA: `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b`
- B4 work-plan blob SHA: `84c94c82ac5b0fde7c7bdf94acca235402c465ab`
- Backend master blob SHA: `f8d9cd456568cc6c8eaae0caf764123a7e859ba6`
- B4 research register blob SHA: `fe1deafb694534743447d9113ae52930d8b68d02`
- Physical-schema manifest blob SHA: `935cd4950d5e8de117a349ac3608cf4e7b663462`
- Target recovery evidence blob SHA: `9798c2b964426dd37f190108460f9120a6174555`
- Post-transition state blob SHA: `3482877a8e321f9d81782270bb44cfaeec297496`

## 2. GitHub Actions identity

- Workflow: `HOMIO Backend and ACRL Runtime CI`
- Run ID: `45808014761`
- Attempt: `1`
- Run URL: [45808014761](https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/45808014761)
- Verification job ID: `139869027065`
- Verification job conclusion: `success`
- Exact tested source SHA: `17784ada3e96edc5182cebb9cc548b2266b40296`
- Verification job checked out the exact triggering commit: **PASS**
- Backend/T21/ACRL verification dependency: **PASS**

## 3. Environment and commands

- Node.js: `24`
- Python: `3.12`
- PostgreSQL: `18.4`
- Redis: `8.0.3`
- Backend command: `npm ci --no-audit --fund=false && npm run verify`
- `npm run verify`: lint, typecheck, Vitest and reproducible build verification
- PostgreSQL integration and recovery: existing verification workflow scripts and B4 Vitest integration tests
- Redis integration: existing Redis 8 distributed rate-limit verifier and Vitest tests
- ACRL: complete existing ACRL regression suite

## 4. Test execution

- Vitest files: `24/24 passed`
- Vitest test cases: `201/201 passed`
- Failed tests: `0`
- Skipped tests: `0`
- Blocked tests: `0`
- Complete ACRL regression: `1466 passed`
- B1 reproducible build verification: `PASS`

### Required B4 test file results

| Test owner | Tests passed |
|---|---:|
| ARCH-037 physical schema integration | 12 |
| B4 full-database recovery integration | 1 |
| Ordered PostgreSQL migration validation | 26 |
| Durable session integration | 3 |
| Security audit integration | 7 |
| Global PostgreSQL transaction owner | 3 |
| PostgreSQL runtime role safety | 7 |
| Shared Redis rate-limit tests | 8 |
| Production persistence composition | 5 |
| CORE-002 transactional outbox | 1 |
| PostgreSQL runtime and transaction owner | 12 |
| Production runtime wiring | 6 |
| Dependency failure readiness | 1 |
| API security regression | 25 |

## 5. Canonical migration inventory and checksums

The guard recomputed SHA-256 from the exact UTF-8 SQL file bytes and verified the existing migration-runner manifest. IDs are contiguous and ordered from `00000001` through `00000011`.

| Migration ID | SQL migration | SHA-256 | Bytes |
|---|---|---|---:|
| `00000001` | `00000001-core002-event-outbox.sql` | `49e6e2d7bccde078df47ca22a7c01f630596ef6d16c09d9ff0741df9a9216203` | 6620 |
| `00000002` | `00000002-core002-safe-tenant-context.sql` | `fdd73252087e6920aa1de7cdad08e4b8197e2a7ac20b82e862815f7e92018e32` | 1036 |
| `00000003` | `00000003-b4-durable-api-sessions.sql` | `54284ed7ef2607a57828a3a4d6e8f30d862de764f7e05573181a1116de8d16b2` | 5424 |
| `00000004` | `00000004-b4-minimized-security-audit.sql` | `fc3c5de7e86e30126c394b91d4a20f85e0ffd93a8386b54f3a0fab14fdb1d3de` | 2028 |
| `00000005` | `00000005-core001-identity-tenant.sql` | `233fae3e95328ea1210f01993025d1aa4e1681c76af20e02703ea85290db6852` | 13717 |
| `00000006` | `00000006-core003-lead-ownership.sql` | `9231350d4aeb6c73a5d3bed8cef28fc079a249b0f00d33f9764cd26efb527457` | 8443 |
| `00000007` | `00000007-core004-inventory.sql` | `c1e46540126d8ee048b8b1793bb440add5df970a8912408d0067207427cffaf0` | 6312 |
| `00000008` | `00000008-core006-deal-transaction.sql` | `d69a681d60f6070fbd1b91687bad53b635405edd1efaa599bc6fc9d6494c79df` | 6915 |
| `00000009` | `00000009-core007-trust-governance.sql` | `023e7893f32bbae9e3bf9aab9766980295dc3208e22ab40e0c215a9973db29f5` | 10227 |
| `00000010` | `00000010-core008-financial.sql` | `0815e3afafa7582e84f66b3268a9a61cbdcbc17379390767a3d1a7e06d6454ea` | 9256 |
| `00000011` | `00000011-b4-security-audit-tenant-write-guard.sql` | `5497c17b3b7d6290643cf7776d273459dd8831607d8b11120d340f203773e8b9` | 5952 |

## 6. Physical schema and canonical ownership

| PostgreSQL schema | Canonical owner |
|---|---|
| `core001` | CORE-001 — identity, tenant and membership |
| `core002` | CORE-002 — event envelope and transactional outbox |
| `core003` | CORE-003 — lead and ownership |
| `core004` | CORE-004 — project and inventory |
| `core006` | CORE-006 — deal and transaction |
| `core007` | CORE-007 — trust, fraud and governance |
| `core008` | CORE-008 — commission and financial ledger |
| `reos_infra` | B4 — sessions, audit, migration and database infrastructure |

The physical-schema manifest maps canonical source owners, relations, columns, constraints and indexes. The guard verifies the manifest SHA and required owner mapping. CORE-005 remains owned by search/retrieval infrastructure and is not introduced as a second PostgreSQL business owner.

## 7. Persistence security and transaction proof

- Migration role and application role separation: **PASS**
- Runtime-role safety and least privilege: **PASS**
- ENABLE RLS and FORCE RLS on tenant-bearing relations: **PASS**
- Fail-closed empty/malformed tenant context: **PASS**
- Cross-tenant read/write denial: **PASS**
- One existing `PostgresRuntime` transaction owner: **PASS**
- No duplicate migration runner or schema authority: **PASS**
- Durable session and revocation persistence: **PASS**
- Minimized append-only security audit persistence: **PASS**
- Redis 8 shared rate-limit concurrency and TTL reset: **PASS**

## 8. Current full-database recovery result

- Source database: `homio_b4_recovery_c72642cb1559aa88`
- Separate restore database: `homio_b4_restore_c72642cb1559aa88`
- Backup SHA-256: `ac480f8b629dc729ea3827b10582b963ec5def35e501eca6d17611660a45b624`
- Backup size: `113621` bytes
- Schema SHA-256: `d5ede408a0598a3815aaafb2d2d066cdfd616d7dd666d789308a90215350c1f1`
- Canonical migration count: `11`
- Replay-applied migration count: `0`
- Schema integrity: **PASS**
- Data integrity: **PASS**
- Tenant isolation after restore: **PASS**
- Database ACL and role/grant integrity: **PASS**
- Target classification: `EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4`
- Controlled non-production target restore: `NOT_VERIFIED`
- Production disaster-recovery exercise: `NOT_TESTED`
- WAL/PITR: `NOT_TESTED`

The restore ran against a separate database inside the disposable GitHub Actions PostgreSQL 18.4 service. It is not evidence of an independently hosted target, production backup encryption, retention, key management, WAL archiving or PITR. The companion evidence file preserves these classifications:

`REOS_CONTROL_CENTER/evidence/BACKEND-001/B4-target-backup-restore-evidence.md`

## 9. The eight B4 acceptance criteria

| Criterion | Guarded completion evidence |
|---|---|
| B4-AC01 — approved ARCH-037 schema and canonical owners | Physical-schema mapping, canonical owners and exact source manifest verified. |
| B4-AC02 — deterministic ordered migrations and integrity | 11 ordered migrations and exact SQL SHA-256 checksums verified; restore ledger matched; replay applied zero migrations. |
| B4-AC03 — tenant access at persistence boundary | PostgreSQL role safety, ENABLE/FORCE RLS and cross-tenant isolation checks passed. |
| B4-AC04 — explicit repository and transaction write ownership | Existing `PostgresRuntime` transaction owner and global transaction tests passed; no parallel persistence owner introduced. |
| B4-AC05 — durable session and revocation storage | Session integration and full restore checks passed. |
| B4-AC06 — shared rate limit and minimized audit persistence | Redis distributed concurrency/TTL and append-only security-audit tests passed. |
| B4-AC07 — migration, concurrency, backup and recovery | Migration, concurrency and full separate-database backup/restore passed on disposable CI PostgreSQL. |
| B4-AC08 — no second schema or persistence authority | Existing runtime, migration runner, ARCH-037 and CORE owners reused; source allowlist rejects new competing owners. |

## 10. Guarded owner authorization

- Owner push and exact commit prefix: **PASS**
- Immutable owner identity: `prajaktaranjane80-sketch` / `320960487`
- Repository identity: `prajaktaranjane80-sketch/Homio` / `1346051793`
- OIDC issuer: `https://token.actions.githubusercontent.com`
- OIDC subject: `repo:prajaktaranjane80-sketch@320960487/Homio@1346051793:ref:refs/heads/reos-development`
- T15: `PROPOSE`
- T15 request fingerprint: `1cd4d216e2c3f973ae5bb4271b00e51d60bdba9eb887e2eea8d8f00950fc13ae`
- T17: `ANALYZE`
- T17 impact fingerprint: `eca099423a0c810567b267fa8956131d0c2ab8b313df42e4866a0d1524e09cc7`
- T17 changed source paths: `2`
- T17 unknown/protected paths: `0/0`
- T18: `AUTHORIZE`
- T18 authorization fingerprint: `8c69ab35ee6fb227a37ecd7944a9f57097826b1fb1643cca977ddeba54039111`
- OIDC bearer token persisted: **NO**

## 11. Canonical Control Center result

- BACKEND-001-B0: `DONE`
- BACKEND-001-B1: `DONE`
- BACKEND-001-B2-FOUNDATION: `DONE`
- BACKEND-001-B3: `DONE`
- BACKEND-001-B4: `DONE`
- BACKEND-001-B2-PRODUCTION-BINDING: `CURRENT`
- BACKEND-001-B5 through B10: `PENDING`
- BACKEND-001-AC01 through AC10: `PENDING`
- BACKEND-001 gate: remains `CURRENT`; the full backend gate is not closed

## 12. GitHub Actions artifacts

| Artifact ID | Name | Expired |
|---:|---|---|
| `15109783573` | `homio-ai-section14-quality-evaluation-17784ada3e96edc5182cebb9cc548b2266b40296-45808014761-1` | `False` |
| `15109244577` | `homio-acrl-audit-resume-17784ada3e96edc5182cebb9cc548b2266b40296-45808014761-1` | `False` |

No B4 backup archive is claimed as an Actions artifact. The backup identity and digest are recorded in the job log and in the B4 target recovery evidence.

## 13. Production-readiness boundary

B4 completion does not grant whole-backend release approval. The workflow product release evaluation reported `PRODUCTION_RELEASE_READY=false` and `PRODUCTION_RELEASE_BLOCKERS=18`. Production security controls, controlled target recovery and PITR remain outside the verified disposable-CI recovery scope.

## 14. Guard and readback decision

- Existing Control Center `cmd_complete_subtask`: **USED**
- Manual `state.json` editing: **NOT PERFORMED**
- Guarded B4 subtask transition: **PASS**
- Next current task: `BACKEND-001-B2-PRODUCTION-BINDING`
- Exact source SHA and run/attempt binding: **PASS**
- Remote branch/state/evidence/packet readback: **CHECKED AFTER GUARDED PUSH; REQUIRED FOR JOB SUCCESS**

The guarded job pushes the Controller-produced transition commit, fetches the canonical branch again, and validates the remote commit SHA, state blob SHA, evidence markers and handoff packet markers. The workflow reports transition PASS only after all remote readbacks succeed.
