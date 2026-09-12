from .completion_models import ProofReport

def evaluate_proof(evidence: dict[str, bool], required: tuple[str, ...]) -> ProofReport:
    passed = tuple(sorted(k for k in required if evidence.get(k) is True))
    failed = tuple(sorted(k for k in required if evidence.get(k) is False))
    missing = tuple(sorted(k for k in required if k not in evidence))
    return ProofReport(passed=passed, failed=failed, missing=missing)
