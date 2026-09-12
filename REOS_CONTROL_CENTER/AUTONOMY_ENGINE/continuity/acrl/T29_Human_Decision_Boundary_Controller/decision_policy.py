from .decision_models import DecisionPolicy


def validate_policy(policy: DecisionPolicy) -> None:
    if not policy.policy_version.strip():
        raise ValueError("policy_version required")

    if policy.max_decision_age < 0:
        raise ValueError("max_decision_age must be non-negative")

    if not isinstance(policy.require_human_for_unresolved, bool):
        raise ValueError("require_human_for_unresolved must be bool")

    if not isinstance(policy.require_human_for_critical, bool):
        raise ValueError("require_human_for_critical must be bool")

    if not isinstance(policy.allow_expiration, bool):
        raise ValueError("allow_expiration must be bool")
