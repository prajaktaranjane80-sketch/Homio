from .completion_controller import evaluate_completion
from .mission_models import MissionSnapshot
def test_completion_controller():
    m=MissionSnapshot('M','objective',('CODE','TEST'),('A',))
    r=evaluate_completion(m,evidence={'CODE':True,'TEST':True},dependency_graph={},completed_nodes={'A'})
    assert r.state.value=='COMPLETED'
