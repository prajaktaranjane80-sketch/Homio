from __future__ import annotations

from .impact_models import (
    ChangeImpactReport,
    T17Metrics,
)


def metrics(
    report: ChangeImpactReport,
) -> T17Metrics:
    return T17Metrics.from_report(
        report
    )


__all__ = [
    "T17Metrics",
    "metrics",
]
