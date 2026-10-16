from __future__ import annotations

from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (
    ExecutionAuthorization,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_registry import (
    AuthorizationDecision,
    AuthorizationReason,
)

from .patch_engine import patch_fingerprint
from .patch_verification import tree_fingerprint
from .repair_models import (
    RepairRequest,
    VerificationEvidence,
)
from .repair_transaction import (
    execute_repair_transaction,
)


def _authorization() -> ExecutionAuthorization:
    return ExecutionAuthorization(
        schema_version="1.0",
        decision=AuthorizationDecision.AUTHORIZE,
        reason=AuthorizationReason.VALIDATED,
        authorization_fingerprint="a" * 64,
        request_fingerprint="b" * 64,
        operator_request_fingerprint="c" * 64,
        impact_fingerprint="d" * 64,
        action_type=None,
        risk=None,
        execution_authorized=True,
        state_mutated=False,
        requires_external_executor=True,
    )


def _patch() -> str:
    return (
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "@@ -1 +1 @@\n"
        "-VALUE = 1\n"
        "+VALUE = 2\n"
    )


def _request(
    root: Path,
    repair_id: str,
) -> RepairRequest:
    return RepairRequest(
        repair_id=repair_id,
        authorization_fingerprint="a" * 64,
        authorization_nonce=f"nonce-{repair_id}",
        diagnosis_fingerprint="b" * 64,
        impact_fingerprint="d" * 64,
        baseline_fingerprint=tree_fingerprint(root),
        allowed_paths=("src/app.py",),
        forbidden_paths=(),
        candidate_patch=_patch(),
    )


def test_transaction_requires_external_verification(
    tmp_path: Path,
):
    source = tmp_path / "src"
    source.mkdir()

    file = source / "app.py"
    file.write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    request = _request(
        tmp_path,
        "repair-003",
    )

    result = execute_repair_transaction(
        repository_root=tmp_path,
        authorization=_authorization(),
        request=request,
    )

    assert result.decision.value == "REPAIR_APPLIED"
    assert result.reason.value == "VERIFICATION_REQUIRED"
    assert result.candidate_patch == ""

    # T20 must not change the main source repository.
    assert file.read_text(
        encoding="utf-8"
    ) == "VALUE = 1\n"


def test_verified_transaction_is_reported(
    tmp_path: Path,
):
    source = tmp_path / "src"
    source.mkdir()

    file = source / "app.py"
    file.write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    request = _request(
        tmp_path,
        "repair-004",
    )

    evidence = VerificationEvidence(
        syntax_passed=True,
        tests_passed=True,
        regression_passed=True,
        external_executor="external-test-runner",
        evidence_fingerprint="e" * 64,
    )

    result = execute_repair_transaction(
        repository_root=tmp_path,
        authorization=_authorization(),
        request=request,
        evidence=evidence,
    )

    assert result.decision.value == "VERIFIED"
    assert result.reason.value == "VALID"
    assert result.candidate_patch == request.candidate_patch
    assert (
        result.patch_fingerprint
        == patch_fingerprint(request.candidate_patch)
    )
    assert result.verification is not None
    assert result.verification.passed is True

    # The verified result is data; main source remains untouched.
    assert file.read_text(
        encoding="utf-8"
    ) == "VALUE = 1\n"
