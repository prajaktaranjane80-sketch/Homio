
REOS AUTONOMOUS ENGINE
======================

Purpose
-------
A code-enforced autonomy layer for HOMIO/REOS_CONTROL_CENTER.

Core principles
---------------
1. Machine state is authoritative.
2. Frozen architecture is protected.
3. Unknown is a first-class state.
4. No semantic mismatch is declared without proof.
5. Large files are never requested by default.
6. The agent extracts only the smallest required evidence.
7. The agent cannot approve, transition, repair, or mutate state unless the control plane explicitly permits it.
8. Every important action has preflight, evidence, execution, postflight, and audit phases.
9. Research is required for current technology/security/vendor facts.
10. Conversation history is not project memory.

Design inspiration
------------------
- Reasoning/action loop + context management + security validation
- Tool-level guardrails and tracing
- Persistent repository-wide / path-specific agent rules
- Agentic threat modeling and trustworthy AI lifecycle controls

IMPORTANT
---------
This engine is intentionally conservative and read-only until integrated
with the existing REOS Control Center command surface.

It does NOT replace reos_control_center.py.
It sits above it as a policy/intelligence layer.

Recommended target integration:

CHAT / AGENT
    |
    v
REOS AUTONOMOUS ENGINE
    |
    +--> Context compiler
    +--> Evidence ledger
    +--> Semantic consistency engine
    +--> Research policy
    +--> Red-team policy
    +--> Execution guard
    +--> Recovery policy
    |
    v
REOS_CONTROL_CENTER
    |
    v
state / gates / transitions

Initial installation
--------------------
Copy this directory under:

D:\HOMIO\REOS_CONTROL_CENTER\REOS_AUTONOMOUS_ENGINE

Then run:

python REOS_AUTONOMOUS_ENGINE\cli.py context
python REOS_AUTONOMOUS_ENGINE\cli.py doctor
python REOS_AUTONOMOUS_ENGINE\cli.py next

Do not connect mutation commands until the existing Control Center
command semantics have been inspected and adapter-tested.
