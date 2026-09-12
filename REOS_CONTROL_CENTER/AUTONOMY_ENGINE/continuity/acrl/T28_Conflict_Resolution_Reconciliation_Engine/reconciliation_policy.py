from reconciliation_models import ReconciliationPolicy


def validate_policy(policy: ReconciliationPolicy) -> None:
    if not policy.policy_version.strip():
        raise ValueError("policy_version required")

    if not isinstance(policy.require_evidence_for_high_conflict, bool):
        raise ValueError("require_evidence_for_high_conflict must be bool")

    if not isinstance(policy.allow_precedence_resolution, bool):
        raise ValueError("allow_precedence_resolution must be bool")

    if not isinstance(policy.allow_human_boundary, bool):
        raise ValueError("allow_human_boundary must be bool")
