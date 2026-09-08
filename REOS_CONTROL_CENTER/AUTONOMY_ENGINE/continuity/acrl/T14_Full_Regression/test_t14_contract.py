from .regression_layer import RegressionLayerEngine, RegressionDecision
from .regression_policy import RegressionPolicy

def test_contract_schema_and_manifest():
    assert RegressionLayerEngine.SCHEMA_VERSION=='1.0'
    assert len(RegressionLayerEngine.LAYER_SPECS)==14
    RegressionPolicy().validate()

def test_contract_has_read_only_surface():
    assert not hasattr(RegressionLayerEngine,'execute_project')
    assert not hasattr(RegressionLayerEngine,'mutate_state')

def test_report_contains_security_metadata():
    assert {'metrics','policy_schema','provenance_fingerprint','compatibility'} <= set(RegressionLayerEngine.build_report([]).to_dict())
