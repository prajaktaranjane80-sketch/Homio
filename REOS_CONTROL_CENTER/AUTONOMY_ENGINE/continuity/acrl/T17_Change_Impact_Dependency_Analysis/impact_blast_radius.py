from __future__ import annotations

from .impact_models import ChangeImpactReport


def blast_radius(
    report: ChangeImpactReport,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            set(
                report.impacted_paths
            )
        )
    )


__all__ = [
    "blast_radius",
]
