"""ACRL T13 — Controller Integration Metrics."""

from dataclasses import dataclass
from typing import Iterable

from .controller_integration import (
    ControllerIntegrationReason,
    ControllerIntegrationReport,
)


@dataclass(frozen=True)
class ControllerMetrics:
    total_integrations: int
    integrated: int
    blocked: int
    fail_closed: int
    gate_conflicts: int
    subtask_conflicts: int
    checkpoint_conflicts: int
    integrity_conflicts: int
    architecture_conflicts: int
    resume_not_safe: int
    authority_conflicts: int
    metric_version: str = "T13-METRICS-1.0"

    def to_dict(self) -> dict[str, int | str]:
        return {
            "metric_version": self.metric_version,
            "total_integrations": self.total_integrations,
            "integrated": self.integrated,
            "blocked": self.blocked,
            "fail_closed": self.fail_closed,
            "gate_conflicts": self.gate_conflicts,
            "subtask_conflicts": self.subtask_conflicts,
            "checkpoint_conflicts": self.checkpoint_conflicts,
            "integrity_conflicts": self.integrity_conflicts,
            "architecture_conflicts": self.architecture_conflicts,
            "resume_not_safe": self.resume_not_safe,
            "authority_conflicts": self.authority_conflicts,
        }


class ControllerMetricsEngine:
    METRICS_VERSION = "T13-METRICS-1.0"

    @classmethod
    def summarize(
        cls,
        reports: Iterable[ControllerIntegrationReport],
    ) -> ControllerMetrics:
        counters = {
            "total_integrations": 0,
            "integrated": 0,
            "blocked": 0,
            "fail_closed": 0,
            "gate_conflicts": 0,
            "subtask_conflicts": 0,
            "checkpoint_conflicts": 0,
            "integrity_conflicts": 0,
            "architecture_conflicts": 0,
            "resume_not_safe": 0,
            "authority_conflicts": 0,
        }

        for report in reports:
            counters["total_integrations"] += 1

            decision = (
                report.decision.value
                if hasattr(report.decision, "value")
                else str(report.decision)
            )

            reason = (
                report.reason.value
                if hasattr(report.reason, "value")
                else str(report.reason)
            )

            if decision == "INTEGRATED":
                counters["integrated"] += 1

            if decision == "BLOCKED":
                counters["blocked"] += 1

            if decision == "FAIL_CLOSED":
                counters["fail_closed"] += 1

            if reason == ControllerIntegrationReason.GATE_CONFLICT.value:
                counters["gate_conflicts"] += 1

            if reason == ControllerIntegrationReason.SUBTASK_CONFLICT.value:
                counters["subtask_conflicts"] += 1

            if reason == ControllerIntegrationReason.CHECKPOINT_CONFLICT.value:
                counters["checkpoint_conflicts"] += 1

            if reason == ControllerIntegrationReason.INTEGRITY_CONFLICT.value:
                counters["integrity_conflicts"] += 1

            if reason == ControllerIntegrationReason.ARCHITECTURE_CONFLICT.value:
                counters["architecture_conflicts"] += 1

            if reason == ControllerIntegrationReason.RESUME_NOT_SAFE.value:
                counters["resume_not_safe"] += 1

            if reason == ControllerIntegrationReason.AUTHORITY_CONFLICT.value:
                counters["authority_conflicts"] += 1

        return ControllerMetrics(
            **counters,
            metric_version=cls.METRICS_VERSION,
        )

    @classmethod
    def from_report(
        cls,
        report: ControllerIntegrationReport,
    ) -> dict[str, int | str]:
        return cls.summarize([report]).to_dict()