"""ACRL T19 — Intelligent Test Selection & Failure Diagnosis."""

from .failure_diagnosis import (
    diagnose_failure,
    diagnose_failures,
)
from .selection_engine import (
    T19TestSelectionEngine,
    discover_tests,
    select_tests,
)
from .t19_models import (
    DiagnosisCandidate,
    FailureCategory,
    FailureDiagnosis,
    FailureEvidence,
    FailureSeverity,
    SelectedTest,
    T19Decision,
    TestCandidate,
    TestPriority,
    TestSelectionPlan,
    TestSelectionReason,
)
from .t19_validation import (
    validate_failure_evidence,
    validate_inputs,
    validate_selection_plan,
)

__all__ = [
    "DiagnosisCandidate",
    "FailureCategory",
    "FailureDiagnosis",
    "FailureEvidence",
    "FailureSeverity",
    "SelectedTest",
    "T19Decision",
    "T19TestSelectionEngine",
    "TestCandidate",
    "TestPriority",
    "TestSelectionPlan",
    "TestSelectionReason",
    "TestCandidate",
    "TestPriority",
    "TestSelectionReason",
    "diagnose_failure",
    "diagnose_failures",
    "discover_tests",
    "select_tests",
    "validate_failure_evidence",
    "validate_inputs",
    "validate_selection_plan",
]
