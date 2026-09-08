from .regression_metrics import summarize
class R:
    def __init__(self, p, tests=1, syntax=False): self.passed=p; self.test_files=tuple([str(i) for i in range(tests)]); self.syntax_error=syntax

def test_summary():
    m=summarize([R(True,2),R(False,1,True)])
    assert (m.total_layers,m.passed_layers,m.failed_layers,m.total_test_files,m.syntax_failures)==(2,1,1,3,1)
