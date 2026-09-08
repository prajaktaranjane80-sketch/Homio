from .regression_policy import RegressionPolicy

def test_default_policy_is_read_only():
    p=RegressionPolicy(); p.validate()
    assert p.allow_source_inspection and p.allow_pytest_plan
    assert not p.allow_test_execution
    assert not p.allow_repository_mutation
    assert not p.allow_controller_mutation
    assert not p.allow_state_mutation
    assert not p.allow_architecture_mutation

def test_mutating_policy_is_rejected():
    p=RegressionPolicy(allow_state_mutation=True)
    try: p.validate()
    except ValueError: return
    assert False
