from __future__ import annotations

from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_autonomy import (
    OperatorAutonomyEngine,
    OperatorRequest,
)
from AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_policy import (
    OperatorActionType,
)
from AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_validation import (
    OperatorContext,
)
from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.change_impact_analysis import (
    ChangeImpactAnalyzer,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_identity import (
    approval_scope_fingerprint,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (
    AuthorizationRequest,
    HumanApproval,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_policy import (
    SafeAuthorizationPolicy,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_registry import (
    AuthorizationDecision,
    AuthorizationReason,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.execution_authorization import (
    ExecutionAuthorizationGuard,
)


def build_operator_report():
    context = OperatorContext(
        gate="CORE-005",
        subtask="CORE-005-T01",
        task="Implement structured search filters.",
        state_available=True,
        state_valid=True,
        architecture_stable=True,
        authority_valid=True,
        integrity_valid=True,
        evidence_available=True,
    )

    request = OperatorRequest(
        context=context,
        requested_action=OperatorActionType.PROPOSE_CHANGE,
        objective="Implement bounded structured search filter support.",
        evidence=("validated_test_evidence",),
    )

    return OperatorAutonomyEngine.operate(request)


def build_impact_report(tmp_path: Path):
    repository = tmp_path / "repo"
    repository.mkdir(exist_ok=True)

    (repository / "x.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    return ChangeImpactAnalyzer(
        repository
    ).analyze(
        ("x.py",)
    )


def build_approved_request(tmp_path: Path):
    operator_report = build_operator_report()
    impact_report = build_impact_report(tmp_path)

    provisional = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce="test-nonce-001",
    )

    approval = HumanApproval(
        approval_id="HUMAN-APPROVAL-001",
        authority="HUMAN_APPROVER",
        approved=True,
        scope_fingerprint=approval_scope_fingerprint(
            provisional
        ),
        evidence=("explicit approval evidence",),
    )

    return AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=approval,
        nonce="test-nonce-001",
    )


def test_policy_is_safe():
    policy = SafeAuthorizationPolicy()
    assert policy.validate() is True
    assert policy.allow_state_mutation is False
    assert policy.allow_execution_by_guard is False
    assert policy.allow_self_approval is False


def test_authorizes_valid_change(tmp_path: Path):
    request = build_approved_request(tmp_path)

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.decision is AuthorizationDecision.AUTHORIZE
    assert artifact.reason is AuthorizationReason.VALIDATED
    assert artifact.execution_authorized is True
    assert artifact.state_mutated is False
    assert artifact.requires_external_executor is True


def test_requires_approval(tmp_path: Path):
    operator_report = build_operator_report()
    impact_report = build_impact_report(tmp_path)

    request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce="missing-approval",
    )

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.decision is AuthorizationDecision.BLOCK
    assert artifact.execution_authorized is False


def test_rejects_unapproved_request(tmp_path: Path):
    operator_report = build_operator_report()
    impact_report = build_impact_report(tmp_path)

    provisional = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce="rejected-approval",
    )

    approval = HumanApproval(
        approval_id="HUMAN-APPROVAL-002",
        authority="HUMAN_APPROVER",
        approved=False,
        scope_fingerprint=approval_scope_fingerprint(
            provisional
        ),
        evidence=("approval declined",),
    )

    request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=approval,
        nonce="rejected-approval",
    )

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.decision is AuthorizationDecision.BLOCK


def test_rejects_t17_unknown_path(tmp_path: Path):
    operator_report = build_operator_report()

    repository = tmp_path / "repo"
    repository.mkdir()

    impact_report = ChangeImpactAnalyzer(
        repository
    ).analyze(
        ("missing.py",)
    )

    provisional = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce="unknown-path",
    )

    approval = HumanApproval(
        approval_id="HUMAN-APPROVAL-003",
        authority="HUMAN_APPROVER",
        approved=True,
        scope_fingerprint=approval_scope_fingerprint(
            provisional
        ),
        evidence=("approval evidence",),
    )

    request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=approval,
        nonce="unknown-path",
    )

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.decision is AuthorizationDecision.BLOCK
    assert artifact.reason is AuthorizationReason.T17_UNKNOWN_PATH


def test_rejects_protected_impact(tmp_path: Path):
    operator_report = build_operator_report()

    repository = tmp_path / "repo"
    repository.mkdir()

    (repository / "state.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    impact_report = ChangeImpactAnalyzer(
        repository
    ).analyze(
        ("state.json",)
    )

    provisional = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce="protected-impact",
    )

    approval = HumanApproval(
        approval_id="HUMAN-APPROVAL-004",
        authority="HUMAN_APPROVER",
        approved=True,
        scope_fingerprint=approval_scope_fingerprint(
            provisional
        ),
        evidence=("approval evidence",),
    )

    request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=approval,
        nonce="protected-impact",
    )

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.decision is AuthorizationDecision.BLOCK
    assert artifact.reason is AuthorizationReason.PROTECTED_IMPACT


def test_rejects_non_change_proposal(tmp_path: Path):
    context = OperatorContext(
        gate="CORE-005",
        subtask="CORE-005-T01",
        task="Observe search implementation.",
        state_available=True,
        state_valid=True,
        architecture_stable=True,
        authority_valid=True,
        integrity_valid=True,
        evidence_available=True,
    )

    operator_request = OperatorRequest(
        context=context,
        requested_action=OperatorActionType.OBSERVE,
        objective="Observe current implementation.",
        evidence=("evidence",),
    )

    operator_report = OperatorAutonomyEngine.operate(
        operator_request
    )

    impact_report = build_impact_report(tmp_path)

    request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce="observational-action",
    )

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.decision is AuthorizationDecision.BLOCK


def test_nonce_changes_authorization_identity(tmp_path: Path):
    first = build_approved_request(tmp_path)

    second = AuthorizationRequest(
        operator_report=first.operator_report,
        impact_report=first.impact_report,
        approval=first.approval,
        nonce="different-nonce-002",
    )

    guard = ExecutionAuthorizationGuard()

    artifact_one = guard.authorize(first)
    artifact_two = guard.authorize(second)

    assert (
        artifact_one.authorization_fingerprint
        != artifact_two.authorization_fingerprint
    )


def test_authorization_is_deterministic(tmp_path: Path):
    request = build_approved_request(tmp_path)

    guard = ExecutionAuthorizationGuard()

    first = guard.authorize(request)
    second = guard.authorize(request)

    assert first == second


def test_t18_never_mutates_state(tmp_path: Path):
    repository = tmp_path / "repo"
    repository.mkdir()

    state = repository / "state.json"
    state.write_text(
        "{}\n",
        encoding="utf-8",
    )

    before = state.read_bytes()

    request = build_approved_request(tmp_path)

    ExecutionAuthorizationGuard().authorize(
        request
    )

    assert state.read_bytes() == before


def test_external_executor_is_always_required(tmp_path: Path):
    request = build_approved_request(tmp_path)

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.requires_external_executor is True


def test_authorization_artifact_does_not_mutate_state(tmp_path: Path):
    request = build_approved_request(tmp_path)

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert artifact.state_mutated is False


def test_policy_blocks_guard_execution():
    policy = SafeAuthorizationPolicy()

    assert policy.allow_execution_by_guard is False


def test_policy_blocks_self_approval():
    policy = SafeAuthorizationPolicy()

    assert policy.allow_self_approval is False


def test_authorized_artifact_is_bound_to_upstream_evidence(
    tmp_path: Path,
):
    request = build_approved_request(tmp_path)

    artifact = ExecutionAuthorizationGuard().authorize(
        request
    )

    assert (
        artifact.operator_request_fingerprint
        == request.operator_report.request_fingerprint
    )

    assert (
        artifact.impact_fingerprint
        == request.impact_report.fingerprint
    )
