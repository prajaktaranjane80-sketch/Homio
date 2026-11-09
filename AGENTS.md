# HOMIO / REOS — Repository Agent Bootstrap

This is a thin, auto-discoverable repository bootstrap. It is not a second
Control Center, execution planner, architecture authority or skill router.

## Mandatory startup — every repository-working agent

Before the first engineering response, repository inspection or code change:

1. Discover the engineering skills available in the current agent runtime.
2. When Superpowers is available, read and invoke `using-superpowers` first.
   Do not rely on remembered skill instructions.
3. Follow the canonical engineering policy in
   `REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py`.
4. Refresh the live GitHub `reos-development` branch and record its exact HEAD.
5. Read `REOS_CONTROL_CENTER/data/state.json` from that same live branch.
   Identify the current gate, task, subtask, dependencies and acceptance criteria.
6. Validate the applicable ACRL T07/T14 continuity and repository-intelligence
   boundaries. Reuse them; do not create replacements.
7. Declare exactly one workstream: `BACKEND`, `FRONTEND` or
   `SHARED_INTEGRATION`.
8. Read the selected workstream's existing master reference and inspect the
   exact files, owners, callers, tests and CI wiring before changing code.

## Skill execution

- `AI_AGENT_ENTRYPOINT.py` is the sole repository-owned skill-routing policy.
  Use its `ENGINEERING_SKILL_ROUTING` and current workflow rules.
- Invoke task-specific skills before the corresponding engineering work.
- For bugs and failed tests, use systematic debugging before proposing fixes.
- For implementation, follow test-driven development.
- Before claiming completion, run the required fresh verification.
- Never claim a skill was invoked unless its instructions were actually loaded
  and followed.
- If Superpowers is unavailable in the current runtime, report that limitation
  and use the disciplined fallback workflow.
- Skill availability or invocation is runtime-local. Do not persist plugin
  activation state in `state.json`, ACRL restart data or T14 manifests.

## Authority and scope

- `REOS_CONTROL_CENTER/data/state.json` is the sole execution-state authority.
- GitHub `reos-development` is the canonical committed code and history.
- This file and `AI_AGENT_ENTRYPOINT.py` do not grant task authorization.
- Execute only the currently authorized subtask. Do not invent the next task.
- Plans, chat history, memories and handoff notes cannot override live state.
- Reuse existing domain owners and ACRL responsibilities. Do not introduce
  duplicate identity, tenant, authorization, backend, state or continuity engines.
- Backend owns API contracts. Frontend consumes those contracts.
- `SHARED_INTEGRATION` coordinates boundaries; it is not a third implementation
  owner.

## Repository working method

- Default to owner-controlled GitHub web-editor saves.
- Provide complete file replacements with exact repository paths when a file
  replacement is required.
- Do not perform direct Git writes, commits, pushes or remote API writes unless
  the owner explicitly authorizes that exception in the current turn and all
  applicable ACRL controls permit it.
- PowerShell output is diagnostic evidence only. Do not assume a local
  workstation is the canonical working environment.
- Do not create extra runners, workflows, policy copies or generated files
  when an existing owner or CI path can be reused.

## Completion evidence

Before reporting a change as complete, independently verify:

- the exact saved file content and blob SHA;
- the exact commit SHA on `reos-development`;
- the relevant tests and build output;
- the GitHub Actions run for that exact SHA;
- any remaining acceptance criteria or production blockers.

A passing development CI run does not, by itself, prove production readiness.
