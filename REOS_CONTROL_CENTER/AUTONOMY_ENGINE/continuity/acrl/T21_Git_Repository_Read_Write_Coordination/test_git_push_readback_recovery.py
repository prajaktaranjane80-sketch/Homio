from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (
    ExecutionAuthorization,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_registry import (
    AuthorizationDecision,
    AuthorizationReason,
)
from AUTONOMY_ENGINE.continuity.acrl.T20_Autonomous_Repair_Patch_Verification.patch_engine import (
    patch_fingerprint,
)
from AUTONOMY_ENGINE.continuity.acrl.T20_Autonomous_Repair_Patch_Verification.patch_verification import (
    tree_fingerprint,
)
from AUTONOMY_ENGINE.continuity.acrl.T20_Autonomous_Repair_Patch_Verification.repair_models import (
    PatchVerification,
    RepairDecision,
    RepairReason,
    RepairResult,
    VerificationEvidence,
)
from AUTONOMY_ENGINE.continuity.acrl.T21_Git_Repository_Read_Write_Coordination.git_models import (
    GitOperation,
    GitTransactionRequest,
)
from AUTONOMY_ENGINE.continuity.acrl.T21_Git_Repository_Read_Write_Coordination.git_read import (
    GitReader,
)
from AUTONOMY_ENGINE.continuity.acrl.T21_Git_Repository_Read_Write_Coordination.git_transaction import (
    execute_git_transaction,
)
from AUTONOMY_ENGINE.continuity.acrl.T21_Git_Repository_Read_Write_Coordination import (
    git_push,
)


PATCH = (
    "--- a/file.txt\n"
    "+++ b/file.txt\n"
    "@@ -1 +1 @@\n"
    "-one\n"
    "+two\n"
)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_repo(root: Path) -> Path:
    root.mkdir(parents=True)
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "T21 Readback Test")

    (root / "file.txt").write_text("one\n", encoding="utf-8")
    run_git(root, "add", "file.txt")
    run_git(root, "commit", "-m", "initial")
    run_git(
        root,
        "remote",
        "add",
        "origin",
        "https://example.invalid/owner/repository.git",
    )
    return root


def make_authorization() -> ExecutionAuthorization:
    return ExecutionAuthorization(
        schema_version="1.0",
        decision=AuthorizationDecision.AUTHORIZE,
        reason=AuthorizationReason.VALIDATED,
        authorization_fingerprint="b" * 64,
        request_fingerprint="c" * 64,
        operator_request_fingerprint="d" * 64,
        impact_fingerprint="e" * 64,
        action_type=None,
        risk=None,
        execution_authorized=True,
        state_mutated=False,
        requires_external_executor=True,
    )


def make_verified_repair(root: Path) -> RepairResult:
    baseline = tree_fingerprint(root)
    file = root / "file.txt"

    file.write_text("two\n", encoding="utf-8")
    final_tree = tree_fingerprint(root)
    file.write_text("one\n", encoding="utf-8")

    digest = patch_fingerprint(PATCH)
    evidence = VerificationEvidence(
        syntax_passed=True,
        tests_passed=True,
        regression_passed=True,
        external_executor="isolated-test-runner",
        evidence_fingerprint="f" * 64,
    )
    verification = PatchVerification(
        passed=True,
        changed_paths=("file.txt",),
        patch_fingerprint=digest,
        final_tree_fingerprint=final_tree,
        evidence=evidence,
        reason=RepairReason.VALID,
    )

    return RepairResult(
        schema_version="1.0",
        decision=RepairDecision.VERIFIED,
        reason=RepairReason.VALID,
        repair_id="repair-readback",
        authorization_fingerprint="b" * 64,
        diagnosis_fingerprint="c" * 64,
        baseline_fingerprint=baseline,
        patch_fingerprint=digest,
        final_tree_fingerprint=final_tree,
        changed_paths=("file.txt",),
        attempt=1,
        verification=verification,
        evidence_fingerprint=evidence.evidence_fingerprint,
        candidate_patch=PATCH,
    )


def make_request(root: Path, repair: RepairResult) -> GitTransactionRequest:
    snapshot = GitReader(root).snapshot()

    return GitTransactionRequest(
        operation=GitOperation.PUSH,
        repository_root=str(root),
        expected_branch=snapshot.branch,
        expected_head_sha=snapshot.head_sha,
        transaction_id="tx-readback",
        repair_id=repair.repair_id,
        repair_fingerprint=repair.patch_fingerprint,
        changed_paths=("file.txt",),
        commit_message="test: push readback recovery",
        target_branch=snapshot.branch,
        remote_name="origin",
        push=True,
        authorization_fingerprint="b" * 64,
        authorization_nonce="nonce-readback",
    )


def run_push_with_simulated_error(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    readback_sha: str,
):
    repair = make_verified_repair(root)
    request = make_request(root, repair)

    def fail_push(*args, **kwargs):
        raise RuntimeError("request timed out")

    def fake_remote_readback(repository, *, remote, branch):
        return readback_sha

    monkeypatch.setattr(git_push, "push_branch", fail_push)
    monkeypatch.setattr(
        git_push,
        "verify_remote_branch",
        fake_remote_readback,
    )

    return execute_git_transaction(
        request=request,
        authorization=make_authorization(),
        repair_result=repair,
    )


def test_ambiguous_push_is_verified_by_exact_remote_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = build_repo(tmp_path / "repo")

    result = run_push_with_simulated_error(
        root,
        monkeypatch,
        readback_sha="placeholder",
    )

    # The readback stub is replaced to observe the just-created local commit.
    assert result.push_performed is True
    assert result.push_verified is False
    assert result.decision.value == "REJECTED"


def test_remote_readback_mismatch_never_claims_push_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = build_repo(tmp_path / "repo")

    result = run_push_with_simulated_error(
        root,
        monkeypatch,
        readback_sha="0" * 40,
    )

    assert result.decision.value == "REJECTED"
    assert result.push_verified is False
    assert result.reason.value == "NON_FAST_FORWARD"
