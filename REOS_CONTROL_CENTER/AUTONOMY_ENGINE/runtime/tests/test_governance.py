from __future__ import annotations

from approval_runtime import ApprovalRuntime
from risk_runtime import RiskRuntime


def test_low_risk_read_only_action():
    runtime = RiskRuntime()

    result = runtime.classify(
        "inspect inventory project files",
        mutation=False,
    )

    assert result.level == "LOW"
    assert result.mutation_allowed is False
    assert result.approval_required is False


def test_medium_risk_mutation_is_guarded():
    runtime = RiskRuntime()

    result = runtime.classify(
        "modify inventory database schema",
        mutation=True,
    )

    assert result.level == "MEDIUM"
    assert result.mutation_allowed is False


def test_critical_action_requires_human_approval():
    runtime = RiskRuntime()

    result = runtime.classify(
        "modify commission financial production records",
        mutation=True,
    )

    assert result.level == "CRITICAL"
    assert result.approval_required is True
    assert result.mutation_allowed is False
    assert "HUMAN_APPROVAL_REQUIRED" in result.blockers


def test_approval_blocks_without_explicit_permission():
    runtime = ApprovalRuntime()

    result = runtime.evaluate(
        risk_level="CRITICAL",
        irreversible=True,
        explicit_approval=False,
    )

    assert result.status == "BLOCKED"
    assert result.required is True
    assert result.approved is False


def test_approval_succeeds_with_explicit_permission():
    runtime = ApprovalRuntime()

    result = runtime.evaluate(
        risk_level="CRITICAL",
        irreversible=True,
        explicit_approval=True,
    )

    assert result.status == "APPROVED"
    assert result.approved is True


def test_noncritical_approval_not_required():
    runtime = ApprovalRuntime()

    result = runtime.evaluate(
        risk_level="LOW",
    )

    assert result.status == "NOT_REQUIRED"
    assert result.approved is True
