from __future__ import annotations

import re
from pathlib import Path

from ..T03_State_Reconstruction.state_reconstruction import (
    ExecutionStateSnapshot,
)
from ..T12_Resume_Safety_Validation.resume_safety_validation import (
    ResumeDecision,
    ResumeSafetyReport,
)
from ..T17_Change_Impact_Dependency_Analysis.impact_models import (
    ChangeImpactReport,
)
from .t19_models import (
    FailureEvidence,
    TestSelectionPlan,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class T19ValidationError(ValueError):
    """Base T19 validation error."""


class T19AuthorityError(T19ValidationError):
    """T19 authority boundary error."""


class T19IntegrityError(T19ValidationError):
    """T19 integrity error."""


def validate_inputs(
    state_snapshot: ExecutionStateSnapshot,
    resume_report: ResumeSafetyReport,
    impact_report: ChangeImpactReport,
    repository_root: Path,
) -> None:
    if not isinstance(
        state_snapshot,
        ExecutionStateSnapshot,
    ):
        raise T19ValidationError(
            "T19 requires T03 ExecutionStateSnapshot."
        )

    if state_snapshot.canonical_source != "data/state.json":
        raise T19AuthorityError(
            "T19 requires data/state.json authority."
        )

    if not _SHA256_RE.fullmatch(
        state_snapshot.source_state_sha256
    ):
        raise T19IntegrityError(
            "T03 state fingerprint is invalid."
        )

    if not isinstance(
        resume_report,
        ResumeSafetyReport,
    ):
        raise T19ValidationError(
            "T19 requires T12 ResumeSafetyReport."
        )

    if resume_report.schema_version != "1.0":
        raise T19ValidationError(
            "Unsupported T12 schema version."
        )

    if resume_report.authority != "REOS_CONTROL_CENTER":
        raise T19AuthorityError(
            "T12 authority is invalid."
        )

    if (
        resume_report.decision
        is not ResumeDecision.SAFE_TO_RESUME
        or resume_report.fail_closed
        or not resume_report.validated
    ):
        raise T19AuthorityError(
            "T19 cannot continue from an unsafe T12 state."
        )

    if not isinstance(
        impact_report,
        ChangeImpactReport,
    ):
        raise T19ValidationError(
            "T19 requires T17 ChangeImpactReport."
        )

    if impact_report.schema_version != "1.0":
        raise T19ValidationError(
            "Unsupported T17 schema version."
        )

    if impact_report.state_mutated:
        raise T19AuthorityError(
            "T17 reports state mutation."
        )

    if impact_report.execution_authorized:
        raise T19AuthorityError(
            "T17 cannot authorize execution."
        )

    if not repository_root.is_dir():
        raise T19ValidationError(
            "T19 repository root must be a directory."
        )


def validate_failure_evidence(
    evidence: FailureEvidence,
) -> None:
    if not isinstance(
        evidence,
        FailureEvidence,
    ):
        raise T19ValidationError(
            "Invalid T19 failure evidence."
        )

    for value, field in (
        (evidence.node_id, "node_id"),
        (evidence.test_path, "test_path"),
        (evidence.exception_type, "exception_type"),
        (evidence.message, "message"),
    ):
        if not isinstance(value, str) or not value.strip():
            raise T19ValidationError(
                f"Failure evidence {field} must be non-empty."
            )


def validate_selection_plan(
    plan: TestSelectionPlan,
) -> None:
    if not isinstance(
        plan,
        TestSelectionPlan,
    ):
        raise T19ValidationError(
            "Invalid T19 selection plan."
        )

    if plan.schema_version != "1.0":
        raise T19ValidationError(
            "Unsupported T19 selection-plan schema."
        )


__all__ = [
    "T19AuthorityError",
    "T19IntegrityError",
    "T19ValidationError",
    "validate_failure_evidence",
    "validate_inputs",
    "validate_selection_plan",
]
