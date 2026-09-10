from __future__ import annotations

import hashlib
import json

from .impact_models import ChangeImpactReport


def fingerprint_report(
    report: ChangeImpactReport,
) -> str:
    payload = {
        "schema_version": report.schema_version,
        "changed_paths": list(report.changed_paths),
        "impacts": [
            {
                "relative_path": item.relative_path,
                "impact_level": item.impact_level.value,
                "reason_code": item.reason_code.value,
                "authority": (
                    item.authority.value
                    if item.authority
                    else None
                ),
                "source_kind": item.source_kind,
                "dependency_distance": item.dependency_distance,
            }
            for item in report.impacts
        ],
        "dependencies": [
            {
                "changed_path": item.changed_path,
                "impacted_path": item.impacted_path,
                "distance": item.distance,
                "relationship": item.relationship,
            }
            for item in report.dependency_impacts
        ],
        "protected": list(
            report.protected_paths
        ),
        "unknown": list(
            report.unknown_paths
        ),
        "graph_nodes": report.graph_nodes,
        "graph_edges": report.graph_edges,
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def fingerprint(value) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


__all__ = [
    "fingerprint_report",
    "fingerprint",
]
