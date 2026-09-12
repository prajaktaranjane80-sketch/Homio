from .completion_controller import evaluate_completion
from .mission_models import MissionSnapshot

def test_hidden_residual_work_blocks_completion():
    m=MissionSnapshot('M','objective',('CODE',),('A',),unresolved_nodes=('HIDDEN',))
    r=evaluate_completion(m,evidence={'CODE':True},dependency_graph={},completed_nodes={'A'})
    assert r.state.value in {'INCOMPLETE','BLOCKED'}

def test_human_rejection_is_terminal():
    m=MissionSnapshot('M','objective',('CODE',),('A',),rejected_human_decision=True)
    r=evaluate_completion(m,evidence={'CODE':True},dependency_graph={},completed_nodes={'A'})
    assert r.state.value=='BLOCKED'
