from .completion_models import ProofReport

def quorum_passed(report: ProofReport, ratio: float = 1.0) -> bool:
    total = len(report.passed) + len(report.failed) + len(report.missing)
    if total == 0:
        return False
    return not report.failed and not report.missing and (len(report.passed) / total) >= ratio
