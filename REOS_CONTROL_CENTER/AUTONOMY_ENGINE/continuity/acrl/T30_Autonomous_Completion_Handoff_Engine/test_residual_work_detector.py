from .mission_models import MissionSnapshot
from .completion_models import ProofReport
from .residual_work_detector import detect_residual_work
def test_residual():
    m=MissionSnapshot('M','x',unresolved_nodes=('X',)); assert 'X' in detect_residual_work(m,ProofReport(),[])
