from __future__ import annotations

from .impact_models import (
    ChangeImpactReport,
    ImpactIntegrationHandoff,
)


def build_handoff(
    report: ChangeImpactReport,
) -> ImpactIntegrationHandoff:
    return ImpactIntegrationHandoff(
        report_fingerprint=report.fingerprint,
        decision=report.decision.value,
        changed_paths=report.changed_paths,
        impacted_paths=report.impacted_paths,
        ready_for_handoff=report.ready_for_handoff,
    )


__all__ = [
    "ImpactIntegrationHandoff",
    "build_handoff",
]
