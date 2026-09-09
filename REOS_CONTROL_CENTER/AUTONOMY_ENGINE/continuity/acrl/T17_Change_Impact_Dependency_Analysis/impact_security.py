from .change_impact_analysis import ChangeImpactSecurityError

def validate_read_only(report):
    if report.state_mutated or report.execution_authorized:
        raise ChangeImpactSecurityError("T17 must remain read-only")
