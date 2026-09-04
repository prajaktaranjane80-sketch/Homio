"""ACRL T09 — Fingerprint Metrics.

Observational metrics for T09 fingerprint operations.

Metrics never alter:
- authoritative state
- controller state
- gate state
- architecture
- fingerprint source data

They are diagnostic only.
"""

from __future__ import annotations

from dataclasses import dataclass
import json


class FingerprintMetricsError(RuntimeError):
    """Base metrics error."""


@dataclass(frozen=True)
class FingerprintMetrics:
    """Immutable T09 fingerprint metrics."""

    component_count: int
    component_fingerprint_count: int
    serialized_size_bytes: int
    fingerprint_length: int
    verified: bool
    tampered_component_count: int
    missing_component_count: int

    def to_dict(self) -> dict:
        return {
            "component_count": self.component_count,
            "component_fingerprint_count": (
                self.component_fingerprint_count
            ),
            "serialized_size_bytes": (
                self.serialized_size_bytes
            ),
            "fingerprint_length": self.fingerprint_length,
            "verified": self.verified,
            "tampered_component_count": (
                self.tampered_component_count
            ),
            "missing_component_count": (
                self.missing_component_count
            ),
        }


class FingerprintMetricsEngine:
    """Collect observational T09 metrics."""

    @classmethod
    def collect(
        cls,
        snapshot,
        report=None,
    ) -> FingerprintMetrics:
        if not hasattr(snapshot, "components"):
            raise FingerprintMetricsError(
                "Snapshot must expose components."
            )

        if not hasattr(
            snapshot,
            "component_fingerprints",
        ):
            raise FingerprintMetricsError(
                "Snapshot must expose component fingerprints."
            )

        components = snapshot.components
        component_fingerprints = (
            snapshot.component_fingerprints
        )

        serialized_fingerprints = [
            item.to_dict()
            for item in component_fingerprints
        ]

        serialized = json.dumps(
            {
                "components": components,
                "component_fingerprints": (
                    serialized_fingerprints
                ),
                "overall_fingerprint": (
                    snapshot.overall_fingerprint
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        tampered_count = 0
        missing_count = 0
        verified = False

        if report is not None:
            verified = bool(report.verified)
            tampered_count = len(
                report.tampered_components
            )
            missing_count = len(
                report.missing_components
            )

        return FingerprintMetrics(
            component_count=len(components),
            component_fingerprint_count=len(
                component_fingerprints
            ),
            serialized_size_bytes=len(
                serialized.encode("utf-8")
            ),
            fingerprint_length=len(
                snapshot.overall_fingerprint
            ),
            verified=verified,
            tampered_component_count=tampered_count,
            missing_component_count=missing_count,
        )


def collect_fingerprint_metrics(
    snapshot,
    report=None,
) -> FingerprintMetrics:
    """Convenience metrics API."""

    return FingerprintMetricsEngine.collect(
        snapshot,
        report,
    )


__all__ = [
    "FingerprintMetrics",
    "FingerprintMetricsEngine",
    "FingerprintMetricsError",
    "collect_fingerprint_metrics",
]