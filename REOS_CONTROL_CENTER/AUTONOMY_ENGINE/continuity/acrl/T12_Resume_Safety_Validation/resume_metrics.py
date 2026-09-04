from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ResumeMetrics:
    decision: str
    reason: str
    validated: bool
    fail_closed: bool
    request_fingerprint: str
    metric_version: str = "T12-METRICS-1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_version": self.metric_version,
            "decision": self.decision,
            "reason": self.reason,
            "validated": self.validated,
            "fail_closed": self.fail_closed,
            "request_fingerprint": self.request_fingerprint,
        }


class ResumeMetricsEngine:
    METRICS_VERSION = "T12-METRICS-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def from_report(cls, report: Any) -> ResumeMetrics:
        if not hasattr(report, "decision"):
            raise TypeError("Invalid resume report.")

        decision = (
            report.decision.value
            if hasattr(report.decision, "value")
            else str(report.decision)
        )

        return ResumeMetrics(
            decision=decision,
            reason=str(report.reason),
            validated=bool(report.validated),
            fail_closed=bool(report.fail_closed),
            request_fingerprint=str(report.request_fingerprint),
            metric_version=cls.METRICS_VERSION,
        )

    @classmethod
    def summarize(
        cls,
        reports: list[Any] | tuple[Any, ...],
    ) -> Mapping[str, int]:
        summary = {
            "total": 0,
            "safe_to_resume": 0,
            "block_resume": 0,
            "fail_closed": 0,
            "validated": 0,
        }

        for report in reports:
            metrics = cls.from_report(report)
            summary["total"] += 1

            if metrics.decision == "SAFE_TO_RESUME":
                summary["safe_to_resume"] += 1

            if metrics.decision == "BLOCK_RESUME":
                summary["block_resume"] += 1

            if metrics.fail_closed:
                summary["fail_closed"] += 1

            if metrics.validated:
                summary["validated"] += 1

        return summary