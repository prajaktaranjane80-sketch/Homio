from __future__ import annotations

from pathlib import Path

from ..T17_Change_Impact_Dependency_Analysis.impact_models import (
    ChangeImpactReport,
)

from .t19_identity import fingerprint
from .t19_models import (
    DiagnosisCandidate,
    FailureCategory,
    FailureDiagnosis,
    FailureEvidence,
    FailureSeverity,
)


def _normalize(value: str) -> str:
    return value.replace("\\", "/").lstrip("./").lower()


def _correlate(
    evidence: FailureEvidence,
    impact_report: ChangeImpactReport,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
]:
    test_path = _normalize(evidence.test_path)

    changed = tuple(
        path
        for path in impact_report.changed_paths
        if (
            _normalize(path) in test_path
            or Path(_normalize(path)).stem
            in Path(test_path).stem
        )
    )

    impacted = tuple(
        path
        for path in impact_report.impacted_paths
        if (
            _normalize(path) in test_path
            or Path(_normalize(path)).stem
            in Path(test_path).stem
        )
    )

    return changed, impacted


def _classify(
    evidence: FailureEvidence,
) -> tuple[
    FailureCategory,
    FailureSeverity,
]:
    exception = evidence.exception_type.lower()
    message = evidence.message.lower()
    combined = (
        exception
        + " "
        + message
        + " "
        + evidence.traceback.lower()
    )

    if (
        "indentationerror" in exception
        or "syntaxerror" in exception
    ):
        return (
            FailureCategory.SYNTAX,
            FailureSeverity.BLOCKING,
        )

    if (
        "modulenotfounderror" in exception
        or "importerror" in exception
        or "cannot import name" in combined
    ):
        return (
            FailureCategory.IMPORT,
            FailureSeverity.BLOCKING,
        )

    if (
        "permissionerror" in exception
        or "permission denied" in combined
        or "access denied" in combined
    ):
        return (
            FailureCategory.SECURITY,
            FailureSeverity.BLOCKING,
        )

    if (
        "state.json" in combined
        or "authority" in combined
        or "fingerprint" in combined
        or "integrity" in combined
    ):
        return (
            FailureCategory.STATE,
            FailureSeverity.HIGH,
        )

    if (
        "schema" in combined
        or "contract" in combined
        or "unsupported" in combined
    ):
        return (
            FailureCategory.CONTRACT,
            FailureSeverity.HIGH,
        )

    if "assertionerror" in exception:
        return (
            FailureCategory.ASSERTION,
            FailureSeverity.HIGH,
        )

    if "filenotfounderror" in exception:
        return (
            FailureCategory.FIXTURE,
            FailureSeverity.MEDIUM,
        )

    if (
        "timeout" in combined
        or "timed out" in combined
    ):
        return (
            FailureCategory.ENVIRONMENT,
            FailureSeverity.HIGH,
        )

    return (
        FailureCategory.UNKNOWN,
        FailureSeverity.MEDIUM,
    )


def diagnose_failure(
    evidence: FailureEvidence,
    impact_report: ChangeImpactReport,
) -> FailureDiagnosis:
    changed, impacted = _correlate(
        evidence,
        impact_report,
    )

    category, severity = _classify(
        evidence
    )

    candidates: list[DiagnosisCandidate] = []

    if category is FailureCategory.SYNTAX:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=99,
                reason=(
                    "The failure evidence identifies a Python "
                    "syntax or indentation failure."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Inspect the reported source line before "
                    "running broader tests."
                ),
            )
        )

    elif category is FailureCategory.IMPORT:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=95,
                reason=(
                    "The failure indicates an import or module "
                    "resolution problem."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Verify package boundaries, relative imports, "
                    "and changed module names."
                ),
            )
        )

    elif category is FailureCategory.STATE:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=94,
                reason=(
                    "The failure references authoritative state, "
                    "authority, fingerprint, or integrity."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Validate T03/T12 state and integrity evidence "
                    "before further execution."
                ),
            )
        )

    elif category is FailureCategory.CONTRACT:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=92,
                reason=(
                    "The failure contains a schema or contract "
                    "compatibility signal."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Compare the failing interface against the "
                    "upstream contract before changing code."
                ),
            )
        )

    elif category is FailureCategory.ASSERTION:
        confidence = 88

        if changed:
            confidence += 7
        elif impacted:
            confidence += 4

        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=min(
                    confidence,
                    99,
                ),
                reason=(
                    "The failure is a behavioral assertion failure."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Compare expected behavior, actual behavior, "
                    "and the T17 affected path set."
                ),
            )
        )

    elif category is FailureCategory.FIXTURE:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=90,
                reason=(
                    "The failure indicates a missing file or fixture."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Verify fixture paths and test setup before "
                    "modifying production code."
                ),
            )
        )

    elif category is FailureCategory.ENVIRONMENT:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=86,
                reason=(
                    "The failure indicates a runtime or environment "
                    "condition."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Check environment conditions and rerun only "
                    "the affected test after verification."
                ),
            )
        )

    elif category is FailureCategory.SECURITY:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=98,
                reason=(
                    "The failure indicates a security or permission "
                    "boundary violation."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Stop automated change execution and inspect "
                    "the authority boundary."
                ),
            )
        )

    else:
        candidates.append(
            DiagnosisCandidate(
                category=category,
                severity=severity,
                confidence=60,
                reason=(
                    "Available evidence is insufficient for a "
                    "higher-confidence classification."
                ),
                affected_paths=changed or impacted,
                recommended_action=(
                    "Collect the complete traceback and correlate "
                    "it with T17 impact evidence."
                ),
            )
        )

    base = {
        "schema_version": "1.0",
        "node_id": evidence.node_id,
        "category": category.value,
        "severity": severity.value,
        "candidates": [
            item.to_dict()
            for item in candidates
        ],
        "changed_path_correlation": list(changed),
        "impacted_path_correlation": list(impacted),
        "explanation": candidates[0].reason,
    }

    return FailureDiagnosis(
        schema_version="1.0",
        node_id=evidence.node_id,
        category=category,
        severity=severity,
        candidates=tuple(candidates),
        changed_path_correlation=changed,
        impacted_path_correlation=impacted,
        diagnosis_fingerprint=fingerprint(base),
        explanation=candidates[0].reason,
    )


def diagnose_failures(
    evidence: tuple[FailureEvidence, ...],
    impact_report: ChangeImpactReport,
) -> tuple[FailureDiagnosis, ...]:
    return tuple(
        diagnose_failure(
            item,
            impact_report,
        )
        for item in evidence
    )


__all__ = [
    "diagnose_failure",
    "diagnose_failures",
]
