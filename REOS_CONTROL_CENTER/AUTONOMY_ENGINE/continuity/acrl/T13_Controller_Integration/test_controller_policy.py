from .controller_policy import ControllerPolicy, ControllerPolicyEngine


def test_default_policy_is_valid():
    policy = ControllerPolicyEngine.default()

    assert ControllerPolicyEngine.validate(policy) is True
    assert policy.authority == "REOS_CONTROL_CENTER"
    assert policy.reconciliation_allowed is True
    assert policy.resume_authorization_allowed is True


def test_execution_authorization_is_forbidden():
    policy = ControllerPolicyEngine.default()

    assert policy.execution_authorization_allowed is False


def test_all_mutation_capabilities_are_forbidden():
    policy = ControllerPolicyEngine.default()

    assert policy.state_mutation_allowed is False
    assert policy.controller_mutation_allowed is False
    assert policy.architecture_mutation_allowed is False
    assert policy.checkpoint_mutation_allowed is False
    assert policy.authority_promotion_allowed is False
    assert policy.recovery_execution_allowed is False


def test_policy_serialization_is_machine_readable():
    policy = ControllerPolicyEngine.default()
    data = policy.to_dict()

    assert data["version"] == "T13-POLICY-1.0"
    assert data["authority"] == "REOS_CONTROL_CENTER"
    assert data["execution_authorization_allowed"] is False


def test_wrong_policy_version_is_rejected():
    policy = ControllerPolicy(version="T13-POLICY-999.0")

    try:
        ControllerPolicyEngine.validate(policy)
    except ValueError:
        return

    raise AssertionError("Unsupported policy version was accepted.")


def test_wrong_policy_authority_is_rejected():
    policy = ControllerPolicy(authority="FAKE_AUTHORITY")

    try:
        ControllerPolicyEngine.validate(policy)
    except ValueError:
        return

    raise AssertionError("Invalid policy authority was accepted.")


def test_execution_enablement_is_rejected():
    policy = ControllerPolicy(
        execution_authorization_allowed=True,
    )

    try:
        ControllerPolicyEngine.validate(policy)
    except ValueError:
        return

    raise AssertionError("Execution authorization was enabled.")
