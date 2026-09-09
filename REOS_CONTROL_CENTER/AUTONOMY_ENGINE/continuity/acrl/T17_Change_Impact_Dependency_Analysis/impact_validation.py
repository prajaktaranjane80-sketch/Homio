from .change_impact_analysis import ChangeImpactAnalyzer, ChangeImpactReport

def validate_report_contract(engine: ChangeImpactAnalyzer, report: ChangeImpactReport) -> None:
    engine.validate_report(report)
