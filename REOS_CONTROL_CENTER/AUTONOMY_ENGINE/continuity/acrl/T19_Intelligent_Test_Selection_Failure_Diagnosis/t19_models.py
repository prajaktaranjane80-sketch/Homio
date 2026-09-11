from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class T19Decision(str, Enum):
    SELECT = "SELECT"
    FALLBACK = "FALLBACK"
    BLOCK = "BLOCK"
    FAIL_CLOSED = "FAIL_CLOSED"


class TestPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class TestSelectionReason(str, Enum):
    DIRECT_CHANGE = "DIRECT_CHANGE"
    IMPACTED_CHANGE = "IMPACTED_CHANGE"
    IMPORT_MATCH = "IMPORT_MATCH"
    NAME_MATCH = "NAME_MATCH"
    CONTRACT_MATCH = "CONTRACT_MATCH"
    INTEGRATION_MATCH = "INTEGRATION_MATCH"
    REGRESSION_MATCH = "REGRESSION_MATCH"
    FAILURE_RELEVANT = "FAILURE_RELEVANT"
    FALLBACK_SMOKE = "FALLBACK_SMOKE"


class FailureCategory(str, Enum):
    SYNTAX = "SYNTAX"
    IMPORT = "IMPORT"
    CONTRACT = "CONTRACT"
    STATE = "STATE"
    SECURITY = "SECURITY"
    ASSERTION = "ASSERTION"
    FIXTURE = "FIXTURE"
    ENVIRONMENT = "ENVIRONMENT"
    UNKNOWN = "UNKNOWN"


class FailureSeverity(str, Enum):
    BLOCKING = "BLOCKING"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True, slots=True)
class TestCandidate:
    path: str
    imports: tuple[str, ...]
    stem: str
    priority: TestPriority


@dataclass(frozen=True, slots=True)
class SelectedTest:
    path: str
    priority: TestPriority
    reasons: tuple[TestSelectionReason, ...]
    score: int


@dataclass(frozen=True, slots=True)
class TestSelectionPlan:
    schema_version: str
    decision: T19Decision
    selected_tests: tuple[SelectedTest, ...]
    candidate_count: int
    changed_paths: tuple[str, ...]
    impacted_paths: tuple[str, ...]
    state_fingerprint: str
    impact_fingerprint: str
    plan_fingerprint: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "selected_tests": [
                {
                    "path": item.path,
                    "priority": item.priority.value,
                    "reasons": [
                        reason.value
                        for reason in item.reasons
                    ],
                    "score": item.score,
                }
                for item in self.selected_tests
            ],
            "candidate_count": self.candidate_count,
            "changed_paths": list(self.changed_paths),
            "impacted_paths": list(self.impacted_paths),
            "state_fingerprint": self.state_fingerprint,
            "impact_fingerprint": self.impact_fingerprint,
            "plan_fingerprint": self.plan_fingerprint,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class FailureEvidence:
    node_id: str
    test_path: str
    exception_type: str
    message: str
    traceback: str = ""
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "test_path": self.test_path,
            "exception_type": self.exception_type,
            "message": self.message,
            "traceback": self.traceback,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True, slots=True)
class DiagnosisCandidate:
    category: FailureCategory
    severity: FailureSeverity
    confidence: int
    reason: str
    affected_paths: tuple[str, ...]
    recommended_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "affected_paths": list(self.affected_paths),
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True, slots=True)
class FailureDiagnosis:
    schema_version: str
    node_id: str
    category: FailureCategory
    severity: FailureSeverity
    candidates: tuple[DiagnosisCandidate, ...]
    changed_path_correlation: tuple[str, ...]
    impacted_path_correlation: tuple[str, ...]
    diagnosis_fingerprint: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "node_id": self.node_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "candidates": [
                candidate.to_dict()
                for candidate in self.candidates
            ],
            "changed_path_correlation": list(
                self.changed_path_correlation
            ),
            "impacted_path_correlation": list(
                self.impacted_path_correlation
            ),
            "diagnosis_fingerprint": self.diagnosis_fingerprint,
            "explanation": self.explanation,
        }


__all__ = [
    "DiagnosisCandidate",
    "FailureCategory",
    "FailureDiagnosis",
    "FailureEvidence",
    "FailureSeverity",
    "SelectedTest",
    "T19Decision",
    "TestCandidate",
    "TestPriority",
    "TestSelectionPlan",
    "TestSelectionReason",
]
