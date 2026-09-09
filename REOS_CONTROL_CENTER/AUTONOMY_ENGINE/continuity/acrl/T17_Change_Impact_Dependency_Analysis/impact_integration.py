from .change_impact_analysis import ChangeImpactAnalyzer, ChangeImpactReport, ImpactIntegrationHandoff

def build_handoff(report: ChangeImpactReport) -> ImpactIntegrationHandoff:
    return ChangeImpactAnalyzer.build_handoff(report)
