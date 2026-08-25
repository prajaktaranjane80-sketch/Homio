
from __future__ import annotations

FACT_STATES = (
    "PROVEN",
    "VERIFIED",
    "SUPPORTED",
    "LIKELY",
    "UNVERIFIED",
    "UNKNOWN",
    "CONTRADICTED",
)

CHECK_STATES = ("PASS", "WARN", "BLOCK")

SENSITIVE_ACTIONS = {
    "approve_gate",
    "transition_gate",
    "modify_frozen_architecture",
    "repair_state",
    "bulk_transfer",
    "financial_mutation",
    "cross_tenant_access",
    "production_deploy",
}

MUTATING_ACTIONS = SENSITIVE_ACTIONS | {
    "complete_subtask",
    "verify_criterion",
    "write_code",
    "database_migration",
    "publish_event",
    "replay_event",
}
