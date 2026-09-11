from __future__ import annotations

from dataclasses import replace

from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.impact_models import (
    ChangeImpactReport,
)
from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.impact_registry import (
    T17Decision,
)

from .failure_diagnosis import (
    diagnose_failure,
)
from .t19_models import (
    FailureCategory,
    FailureEvidence,
)


def build_impact():
    return ChangeImpactReport(
        schema_version="1.0",
        decision=T17Decision.ANALYZE,
        changed_paths=("execution_authorization.py",),
        impacts=(),
        dependency_impacts=(),
        protected_paths=(),
        unknown_paths=(),
        graph_nodes=1,
        graph_edges=0,
        fingerprint="a" * 64,
        policy_schema="1.0",
        provenance_source="T17",
        state_mutated=False,
        execution_authorized=False,
    )


def test_diagnoses_syntax_failure():
    evidence = FailureEvidence(
        node_id="test_example",
        test_path="test_execution_authorization.py",
        exception_type="IndentationError",
        message="expected an indented block",
    )

    diagnosis = diagnose_failure(
        evidence,
        build_impact(),
    )

    assert diagnosis.category is FailureCategory.SYNTAX
    assert diagnosis.severity.value == "BLOCKING"


def test_diagnoses_import_failure():
    evidence = FailureEvidence(
        node_id="test_example",
        test_path="test_example.py",
        exception_type="ModuleNotFoundError",
        message="No module named 'missing'",
    )

    diagnosis = diagnose_failure(
        evidence,
        build_impact(),
    )

    assert diagnosis.category is FailureCategory.IMPORT


def test_diagnoses_state_failure():
    evidence = FailureEvidence(
        node_id="test_example",
        test_path="test_state.py",
        exception_type="AssertionError",
        message="state.json fingerprint mismatch",
    )

    diagnosis = diagnose_failure(
        evidence,
        build_impact(),
    )

    assert diagnosis.category is FailureCategory.STATE


def test_diagnoses_contract_failure():
    evidence = FailureEvidence(
        node_id="test_example",
        test_path="test_contract.py",
        exception_type="ValueError",
        message="Unsupported schema contract",
    )

    diagnosis = diagnose_failure(
        evidence,
        build_impact(),
    )

    assert diagnosis.category is FailureCategory.CONTRACT


def test_diagnosis_is_deterministic():
    evidence = FailureEvidence(
        node_id="test_example",
        test_path="test_example.py",
        exception_type="AssertionError",
        message="expected 1 got 2",
    )

    first = diagnose_failure(
        evidence,
        build_impact(),
    )

    second = diagnose_failure(
        evidence,
        build_impact(),
    )

    assert first == second


def test_diagnosis_has_fingerprint():
    evidence = FailureEvidence(
        node_id="test_example",
        test_path="test_example.py",
        exception_type="AssertionError",
        message="expected 1 got 2",
    )

    diagnosis = diagnose_failure(
        evidence,
        build_impact(),
    )

    assert len(
        diagnosis.diagnosis_fingerprint
    ) == 64


def test_security_failure_is_high_confidence():
    evidence = FailureEvidence(
        node_id="test_security",
        test_path="test_security.py",
        exception_type="PermissionError",
        message="Access denied",
    )

    diagnosis = diagnose_failure(
        evidence,
        build_impact(),
    )

    assert diagnosis.category is FailureCategory.SECURITY
    assert diagnosis.candidates[0].confidence >= 95
