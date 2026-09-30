"""CORE-007 T03 - Deterministic Risk Assessment Engine.

Consumes:
- CORE-007 T01 TrustScore
- CORE-007 T02 FraudAssessment
- CORE-007 T03 RiskAssessmentPolicy

Produces:
- immutable RiskAssessment

Explicitly excluded:
- governance,
- approval,
- authorization,
- deny/allow decisions,
- sanctions,
- event publishing,
- Control Center state,
- ACRL state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID, uuid4

from .fraud_detection import (
    FraudAssessment,
    FraudFinding,
)
from .risk_assessment import (
    RiskAssessment,
    RiskAssessmentConflictError,
    RiskAssessmentInsufficientEvidenceError,
    RiskAssessmentScopeError,
    RiskAssessmentValidationError,
    RiskEvaluationTrace,
    RiskFactor,
    RiskFactorSource,
    RiskLevel,
)
from .risk_assessment_policy import (
    RiskAssessmentPolicy,
)
from .trust_score import TrustScore


class RiskAssessmentEngine:
    """CORE-007 T03 deterministic assessment authority."""

    MODEL_VERSION = "1.0"

    @staticmethod
    def _max_level(
        first: RiskLevel,
        second: RiskLevel,
    ) -> RiskLevel:
        return (
            first
            if first.rank >= second.rank
            else second
        )

    @staticmethod
    def _validate_scope(
        *,
        tenant_id: str,
        subject_id: str,
        trust_score: TrustScore | None,
        fraud_assessment: FraudAssessment | None,
    ) -> None:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise RiskAssessmentValidationError(
                "tenant_id must be non-empty text."
            )

        if not isinstance(subject_id, str) or not subject_id.strip():
            raise RiskAssessmentValidationError(
                "subject_id must be non-empty text."
            )

        if trust_score is not None:
            if not isinstance(
                trust_score,
                TrustScore,
            ):
                raise RiskAssessmentValidationError(
                    "trust_score must be TrustScore."
                )

            trust_score.assert_scope(
                tenant_id=tenant_id,
                subject_id=subject_id,
            )

        if fraud_assessment is not None:
            fraud_tenant = str(
                fraud_assessment.tenant_id
            )
            fraud_subject = str(
                fraud_assessment.subject_id
            )

            if (
                fraud_tenant != tenant_id
                or fraud_subject != subject_id
            ):
                raise RiskAssessmentScopeError(
                    "Fraud assessment crosses tenant or subject scope."
                )

    @staticmethod
    def _trust_factor(
        *,
        trust_score: TrustScore,
        policy: RiskAssessmentPolicy,
    ) -> tuple[RiskFactor, RiskEvaluationTrace]:
        band = policy.trust_score_rule(
            trust_score.score
        )

        factor = RiskFactor(
            factor_id=(
                "trust-score:"
                f"{trust_score.model_version}:"
                f"{trust_score.model_fingerprint}"
            ),
            source_type=RiskFactorSource.TRUST_SCORE,
            code=band.rule_code,
            raw_value=str(trust_score.score),
            contribution_points=band.contribution_points,
            evidence_references=tuple(
                trust_score.signal_fingerprints
            ),
            source_references=tuple(
                trust_score.signal_ids
            ),
            source_fingerprint=trust_score.fingerprint,
            observed_at=trust_score.computed_at,
        )

        trace = RiskEvaluationTrace(
            factor_id=factor.factor_id,
            rule_reference=band.rule_code,
            input_reference=trust_score.fingerprint,
            contribution_points=band.contribution_points,
            resulting_level=band.risk_level,
            explanation=(
                "Trust score "
                f"{trust_score.score} matched rule "
                f"{band.rule_code}."
            ),
        )

        return factor, trace

    @staticmethod
    def _fraud_factors(
        *,
        fraud_assessment: FraudAssessment,
        policy: RiskAssessmentPolicy,
    ) -> tuple[
        tuple[RiskFactor, ...],
        tuple[RiskEvaluationTrace, ...],
    ]:
        findings = sorted(
            fraud_assessment.findings,
            key=lambda finding: (
                str(finding.finding_id),
                finding.code.value,
                finding.fingerprint,
            ),
        )

        by_id: dict[str, FraudFinding] = {}

        for finding in findings:
            finding_id = str(finding.finding_id)
            existing = by_id.get(finding_id)

            if existing is None:
                by_id[finding_id] = finding
                continue

            if existing.fingerprint != finding.fingerprint:
                raise RiskAssessmentConflictError(
                    "Same fraud finding identity has conflicting "
                    "content."
                )

        unique_findings = tuple(
            by_id[key]
            for key in sorted(by_id)
        )

        if not unique_findings:
            factor = RiskFactor(
                factor_id=(
                    "fraud-assessment:"
                    f"{fraud_assessment.fingerprint}"
                ),
                source_type=RiskFactorSource.FRAUD_ASSESSMENT,
                code="FRAUD_ASSESSMENT_CLEAR",
                raw_value="NO_FINDINGS",
                contribution_points=0,
                evidence_references=(),
                source_references=(
                    fraud_assessment.correlation_id,
                ),
                source_fingerprint=fraud_assessment.fingerprint,
                observed_at=fraud_assessment.generated_at,
            )

            trace = RiskEvaluationTrace(
                factor_id=factor.factor_id,
                rule_reference="FRAUD_ASSESSMENT_CLEAR",
                input_reference=fraud_assessment.fingerprint,
                contribution_points=0,
                resulting_level=RiskLevel.INFORMATIONAL,
                explanation=(
                    "Fraud assessment completed without "
                    "detected findings."
                ),
            )

            return (factor,), (trace,)

        factors: list[RiskFactor] = []
        traces: list[RiskEvaluationTrace] = []

        for finding in unique_findings:
            points = policy.fraud_points(
                finding.severity
            )
            level = policy.fraud_level(
                finding.severity
            )

            factor = RiskFactor(
                factor_id=(
                    "fraud-finding:"
                    f"{finding.finding_id}"
                ),
                source_type=RiskFactorSource.FRAUD_FINDING,
                code=finding.code.value,
                raw_value=finding.severity.value,
                contribution_points=points,
                evidence_references=(
                    finding.evidence_references
                ),
                source_references=(
                    finding.source_references
                ),
                source_fingerprint=finding.fingerprint,
                observed_at=finding.observed_at,
            )

            trace = RiskEvaluationTrace(
                factor_id=factor.factor_id,
                rule_reference=(
                    "FRAUD_SEVERITY:"
                    f"{finding.severity.value}"
                ),
                input_reference=finding.fingerprint,
                contribution_points=points,
                resulting_level=level,
                explanation=(
                    f"Fraud finding {finding.code.value} "
                    f"with severity {finding.severity.value} "
                    f"contributed {points} risk points."
                ),
            )

            factors.append(factor)
            traces.append(trace)

        return (
            tuple(factors),
            tuple(traces),
        )

    def evaluate(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        trust_score: TrustScore | None = None,
        fraud_assessment: FraudAssessment | None = None,
        policy: RiskAssessmentPolicy | None = None,
        assessment_id: UUID | None = None,
        assessment_version: int = 1,
        evaluated_at: datetime | None = None,
    ) -> RiskAssessment:
        if (
            trust_score is None
            and fraud_assessment is None
        ):
            raise RiskAssessmentInsufficientEvidenceError(
                "At least one TrustScore or FraudAssessment "
                "is required."
            )

        if (
            assessment_version < 1
            or isinstance(assessment_version, bool)
        ):
            raise RiskAssessmentValidationError(
                "assessment_version must be an integer >= 1."
            )

        policy = policy or RiskAssessmentPolicy.baseline()

        self._validate_scope(
            tenant_id=tenant_id,
            subject_id=subject_id,
            trust_score=trust_score,
            fraud_assessment=fraud_assessment,
        )

        factors: list[RiskFactor] = []
        traces: list[RiskEvaluationTrace] = []

        if trust_score is not None:
            trust_factor, trust_trace = self._trust_factor(
                trust_score=trust_score,
                policy=policy,
            )
            factors.append(trust_factor)
            traces.append(trust_trace)

        if fraud_assessment is not None:
            fraud_factors, fraud_traces = (
                self._fraud_factors(
                    fraud_assessment=fraud_assessment,
                    policy=policy,
                )
            )
            factors.extend(fraud_factors)
            traces.extend(fraud_traces)

        factors.sort(
            key=lambda factor: (
                factor.source_type.value,
                factor.factor_id,
                factor.fingerprint,
            )
        )

        trace_by_factor = {
            trace.factor_id: trace
            for trace in traces
        }

        ordered_traces = tuple(
            trace_by_factor[factor.factor_id]
            for factor in factors
        )

        total_points = sum(
            factor.contribution_points
            for factor in factors
        )

        risk_score = min(
            100,
            total_points,
        )

        score_level = policy.final_level(
            risk_score
        )

        factor_level = RiskLevel.INFORMATIONAL

        for trace in ordered_traces:
            factor_level = self._max_level(
                factor_level,
                trace.resulting_level,
            )

        final_level = self._max_level(
            score_level,
            factor_level,
        )

        input_fingerprints: set[str] = set()

        if trust_score is not None:
            input_fingerprints.add(
                trust_score.fingerprint
            )

        if fraud_assessment is not None:
            input_fingerprints.add(
                fraud_assessment.fingerprint
            )

        if not input_fingerprints:
            raise RiskAssessmentInsufficientEvidenceError(
                "No source fingerprint available."
            )

        return RiskAssessment(
            assessment_id=assessment_id or uuid4(),
            tenant_id=tenant_id,
            subject_id=subject_id,
            assessment_version=assessment_version,
            risk_score=risk_score,
            risk_level=final_level,
            policy_version=policy.policy_version,
            policy_fingerprint=policy.fingerprint,
            factors=tuple(factors),
            evaluation_trace=ordered_traces,
            input_fingerprints=tuple(
                sorted(input_fingerprints)
            ),
            evaluated_at=(
                evaluated_at
                or datetime.now(timezone.utc)
            ),
        )
