"""CORE-007 Trust, Fraud & Governance package.

Package boundary rules
----------------------
- CORE-001 remains the identity / authorization authority.
- CORE-002 remains the event transport / event infrastructure authority.
- ACRL remains the reconstruction / recovery authority.
- REOS Control Center remains the canonical project-state authority.
- CORE-007 owns trust, fraud, risk and governance domain contracts only.

This module is package wiring only. It does not create a second
business engine, authorization engine, event bus, audit engine,
payment engine, ownership engine, or project-state store.
"""

from .approval_workflow import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalState,
    ApprovalTransitionError,
    ApprovalWorkflow,
    ApprovalWorkflowError,
)

from .dispute_escalation import (
    EscalationError,
    EscalationHook,
    EscalationHooks,
    EscalationLevel,
    EscalationState,
)

from .exception_registry import (
    ExceptionError,
    ExceptionScopeError,
    ExceptionState,
    ExceptionRegistry,
    GovernanceException,
)

from .fraud_detection import (
    FRAUD_DETECTION_MODEL_VERSION,
    FRAUD_DETECTION_SCHEMA_VERSION,
    FraudAssessment,
    FraudDetectionConflictError,
    FraudDetectionEngine,
    FraudDetectionError,
    FraudDetectionPolicy,
    FraudDetectionScopeError,
    FraudDetectionValidationError,
    FraudFinding,
    FraudFindingCode,
    FraudSeverity,
    LeadSubmissionObservation,
    VisitTelemetryObservation,
)

from .governance_acrl_contract import (
    GovernanceACRLError,
    GovernanceACRLArtifact,
    GovernanceACRLArtifactDescriptor,
    GovernanceACRLCheckpoint,
    GovernanceACRLCheckpointError,
    GovernanceACRLContract,
    GovernanceACRLIntegrityError,
    GovernanceACRLScopeError,
)

from .governance_consistency import (
    GOVERNANCE_CONSISTENCY_SCHEMA_VERSION,
    ConsistencyCheck,
    GovernanceConcurrentReviewError,
    GovernanceConsistencyError,
    GovernanceConsistencyGuard,
    GovernanceConsistencySnapshot,
    GovernanceDuplicateCommandError,
    GovernanceDuplicateSignalError,
    GovernanceReplayConflictError,
    GovernanceStaleEvaluationError,
    GovernanceStalePolicyError,
    GovernanceVersionConflictError,
    GovernanceVersionToken,
)

from .governance_decision import (
    GOVERNANCE_DECISION_ENGINE_VERSION,
    GOVERNANCE_DECISION_SCHEMA_VERSION,
    GovernanceAuthorityClass,
    GovernanceDecision,
    GovernanceDecisionConflictError,
    GovernanceDecisionEngine,
    GovernanceDecisionError,
    GovernanceDecisionType,
    GovernanceDecisionValidationError,
    GovernanceEscalationLevel,
    GovernanceEscalationState,
    GovernanceReviewState,
)

from .governance_engine import (
    GovernanceEngine,
    GovernanceEvaluation,
    GovernanceEvaluationConflictError,
    GovernanceEvaluationError,
    GovernanceScopeError,
)

from .governance_event_contract import (
    GOVERNANCE_EVENT_SCHEMA_NAME,
    GOVERNANCE_EVENT_SCHEMA_VERSION,
    GovernanceEventContract,
    GovernanceEventError,
    GovernanceEventScopeError,
    GovernanceEventType,
    build_escalation_event,
    build_fraud_signal_event,
    build_governance_event,
    build_governance_review_event,
    build_override_event,
    build_risk_assessment_event,
    build_trust_signal_event,
)

from .governance_evidence import (
    EvidenceIntegrityError,
    EvidenceLink,
    GovernanceEvidenceEnvelope,
    GovernanceEvidenceError,
)

from .governance_policy import (
    GOVERNANCE_POLICY_ENGINE_VERSION,
    GOVERNANCE_SCHEMA_VERSION,
    GovernanceActionClass,
    GovernanceDisposition,
    GovernancePolicy,
    GovernancePolicyConflictError,
    GovernancePolicyError,
    GovernancePolicyValidationError,
    GovernanceRule,
)

from .governance_reos_contract import (
    CORE007_REOS_CONTRACT_VERSION,
    GovernanceREOSBoundary,
    GovernanceREOSContractError,
    GovernanceREOSExecutionContext,
)

from .governance_security import (
    GOVERNANCE_SECURITY_SCHEMA_VERSION,
    GovernanceActorViolation,
    GovernanceContextViolation,
    GovernancePrivilegeClass,
    GovernanceSecurityBoundary,
    GovernanceSecurityContext,
    GovernanceSecurityError,
    GovernanceSubjectViolation,
    GovernanceTenantViolation,
)

from .risk_assessment import (
    RISK_ASSESSMENT_MODEL_VERSION,
    RISK_ASSESSMENT_SCHEMA_VERSION,
    RISK_SCORE_MAX,
    RISK_SCORE_MIN,
    RiskAssessment,
    RiskAssessmentConflictError,
    RiskAssessmentError,
    RiskAssessmentInsufficientEvidenceError,
    RiskAssessmentScopeError,
    RiskAssessmentValidationError,
    RiskEvaluationTrace,
    RiskFactor,
    RiskFactorSource,
    RiskLevel,
)

from .risk_assessment_engine import (
    RiskAssessmentEngine,
)

from .risk_assessment_policy import (
    RISK_ASSESSMENT_POLICY_SCHEMA_VERSION,
    RISK_ASSESSMENT_POLICY_VERSION,
    RiskAssessmentPolicy,
    RiskScoreLevelBand,
    TrustRiskBand,
)

from .risk_rules import (
    RISK_RULE_ENGINE_VERSION,
    RISK_RULE_SCHEMA_VERSION,
    RiskRule,
    RiskRuleCondition,
    RiskRuleConflictError,
    RiskRuleEngine,
    RiskRuleError,
    RiskRuleEvaluation,
    RiskRuleOutcome,
    RiskRulePolicy,
    RiskRuleScopeError,
    RiskRuleValidationError,
    default_fraud_risk_policy,
)

from .trust_score import (
    TRUST_SCORE_MAX,
    TRUST_SCORE_MIN,
    TRUST_SCORE_MODEL_VERSION,
    TRUST_SCORE_SCHEMA_VERSION,
    TrustScore,
    TrustScoreConflictError,
    TrustScoreContribution,
    TrustScoreDecisionBoundary,
    TrustScoreEngine,
    TrustScoreError,
    TrustScoreInsufficientEvidenceError,
    TrustScoreScopeError,
    TrustScoreValidationError,
    TrustScoringModel,
    TrustSignal,
)


__all__ = [
    # ------------------------------------------------------------------
    # T01 — Trust
    # ------------------------------------------------------------------
    "TRUST_SCORE_MAX",
    "TRUST_SCORE_MIN",
    "TRUST_SCORE_MODEL_VERSION",
    "TRUST_SCORE_SCHEMA_VERSION",
    "TrustScore",
    "TrustScoreConflictError",
    "TrustScoreContribution",
    "TrustScoreDecisionBoundary",
    "TrustScoreEngine",
    "TrustScoreError",
    "TrustScoreInsufficientEvidenceError",
    "TrustScoreScopeError",
    "TrustScoreValidationError",
    "TrustScoringModel",
    "TrustSignal",

    # ------------------------------------------------------------------
    # T02 — Fraud Detection
    # ------------------------------------------------------------------
    "FRAUD_DETECTION_MODEL_VERSION",
    "FRAUD_DETECTION_SCHEMA_VERSION",
    "FraudAssessment",
    "FraudDetectionConflictError",
    "FraudDetectionEngine",
    "FraudDetectionError",
    "FraudDetectionPolicy",
    "FraudDetectionScopeError",
    "FraudDetectionValidationError",
    "FraudFinding",
    "FraudFindingCode",
    "FraudSeverity",
    "LeadSubmissionObservation",
    "VisitTelemetryObservation",

    # ------------------------------------------------------------------
    # T03 — Risk Assessment
    # ------------------------------------------------------------------
    "RISK_ASSESSMENT_MODEL_VERSION",
    "RISK_ASSESSMENT_SCHEMA_VERSION",
    "RISK_SCORE_MAX",
    "RISK_SCORE_MIN",
    "RiskAssessment",
    "RiskAssessmentConflictError",
    "RiskAssessmentEngine",
    "RiskAssessmentError",
    "RiskAssessmentInsufficientEvidenceError",
    "RiskAssessmentPolicy",
    "RiskAssessmentScopeError",
    "RiskAssessmentValidationError",
    "RiskEvaluationTrace",
    "RiskFactor",
    "RiskFactorSource",
    "RiskLevel",
    "RiskScoreLevelBand",
    "TrustRiskBand",
    "RISK_ASSESSMENT_POLICY_SCHEMA_VERSION",
    "RISK_ASSESSMENT_POLICY_VERSION",

    # ------------------------------------------------------------------
    # T03 — Risk Rules
    # ------------------------------------------------------------------
    "RISK_RULE_ENGINE_VERSION",
    "RISK_RULE_SCHEMA_VERSION",
    "RiskRule",
    "RiskRuleCondition",
    "RiskRuleConflictError",
    "RiskRuleEngine",
    "RiskRuleError",
    "RiskRuleEvaluation",
    "RiskRuleOutcome",
    "RiskRulePolicy",
    "RiskRuleScopeError",
    "RiskRuleValidationError",
    "default_fraud_risk_policy",

    # ------------------------------------------------------------------
    # T04/T05 — Governance Policy + Evaluation
    # ------------------------------------------------------------------
    "GOVERNANCE_SCHEMA_VERSION",
    "GOVERNANCE_POLICY_ENGINE_VERSION",
    "GovernanceActionClass",
    "GovernanceDisposition",
    "GovernanceEngine",
    "GovernanceEvaluation",
    "GovernanceEvaluationConflictError",
    "GovernanceEvaluationError",
    "GovernancePolicy",
    "GovernancePolicyConflictError",
    "GovernancePolicyError",
    "GovernancePolicyValidationError",
    "GovernanceRule",
    "GovernanceScopeError",

    # ------------------------------------------------------------------
    # T05/T06 — Decision / Approval / Escalation
    # ------------------------------------------------------------------
    "GOVERNANCE_DECISION_ENGINE_VERSION",
    "GOVERNANCE_DECISION_SCHEMA_VERSION",
    "GovernanceAuthorityClass",
    "GovernanceDecision",
    "GovernanceDecisionConflictError",
    "GovernanceDecisionEngine",
    "GovernanceDecisionError",
    "GovernanceDecisionType",
    "GovernanceDecisionValidationError",
    "GovernanceEscalationLevel",
    "GovernanceEscalationState",
    "GovernanceReviewState",
    "ApprovalDecision",
    "ApprovalRecord",
    "ApprovalRequest",
    "ApprovalState",
    "ApprovalTransitionError",
    "ApprovalWorkflow",
    "ApprovalWorkflowError",
    "EscalationError",
    "EscalationHook",
    "EscalationHooks",
    "EscalationLevel",
    "EscalationState",
    "ExceptionError",
    "ExceptionScopeError",
    "ExceptionState",
    "ExceptionRegistry",
    "GovernanceException",

    # ------------------------------------------------------------------
    # T07 — Evidence
    # ------------------------------------------------------------------
    "EvidenceIntegrityError",
    "EvidenceLink",
    "GovernanceEvidenceEnvelope",
    "GovernanceEvidenceError",

    # ------------------------------------------------------------------
    # T08 — Security / Tenant Boundary
    # ------------------------------------------------------------------
    "GOVERNANCE_SECURITY_SCHEMA_VERSION",
    "GovernanceActorViolation",
    "GovernanceContextViolation",
    "GovernancePrivilegeClass",
    "GovernanceSecurityBoundary",
    "GovernanceSecurityContext",
    "GovernanceSecurityError",
    "GovernanceSubjectViolation",
    "GovernanceTenantViolation",

    # ------------------------------------------------------------------
    # T09 — Consistency / Concurrency
    # ------------------------------------------------------------------
    "GOVERNANCE_CONSISTENCY_SCHEMA_VERSION",
    "ConsistencyCheck",
    "GovernanceConcurrentReviewError",
    "GovernanceConsistencyError",
    "GovernanceConsistencyGuard",
    "GovernanceConsistencySnapshot",
    "GovernanceDuplicateCommandError",
    "GovernanceDuplicateSignalError",
    "GovernanceReplayConflictError",
    "GovernanceStaleEvaluationError",
    "GovernanceStalePolicyError",
    "GovernanceVersionConflictError",
    "GovernanceVersionToken",

    # ------------------------------------------------------------------
    # T10 — REOS Integration
    # ------------------------------------------------------------------
    "CORE007_REOS_CONTRACT_VERSION",
    "GovernanceREOSBoundary",
    "GovernanceREOSContractError",
    "GovernanceREOSExecutionContext",

    # ------------------------------------------------------------------
    # T11 — ACRL Integration
    # ------------------------------------------------------------------
    "GovernanceACRLError",
    "GovernanceACRLArtifact",
    "GovernanceACRLArtifactDescriptor",
    "GovernanceACRLCheckpoint",
    "GovernanceACRLCheckpointError",
    "GovernanceACRLContract",
    "GovernanceACRLIntegrityError",
    "GovernanceACRLScopeError",

    # ------------------------------------------------------------------
    # T12 — Governance Events
    # ------------------------------------------------------------------
    "GOVERNANCE_EVENT_SCHEMA_NAME",
    "GOVERNANCE_EVENT_SCHEMA_VERSION",
    "GovernanceEventContract",
    "GovernanceEventError",
    "GovernanceEventScopeError",
    "GovernanceEventType",
    "build_escalation_event",
    "build_fraud_signal_event",
    "build_governance_event",
    "build_governance_review_event",
    "build_override_event",
    "build_risk_assessment_event",
    "build_trust_signal_event",
]
