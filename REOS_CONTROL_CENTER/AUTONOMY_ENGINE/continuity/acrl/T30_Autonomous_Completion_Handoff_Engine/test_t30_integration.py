from .completion_controller import evaluate_completion
from .mission_models import MissionSnapshot

def test_handoff_ready():
    m=MissionSnapshot('M','objective',('CODE',),('A',))
    r=evaluate_completion(m,evidence={'CODE':True},dependency_graph={},completed_nodes={'A'},candidates=[{'mission_id':'NEXT','ready':True,'priority':5}])
    assert r.state.value=='HANDOFF_READY' and r.next_mission=='NEXT'
