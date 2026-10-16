from __future__ import annotations

import subprocess
from pathlib import Path

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

from .git_models import (
    GitOperation,
    GitTransactionRequest,
)
from .git_lock import GitTransactionLock
from .git_read import GitReader
from .git_transaction import execute_git_transaction
from .git_stage import staged_paths


PATCH = (
    "--- a/file.txt\n"
    "+++ b/file.txt\n"
    "@@ -1 +1 @@\n"
    "-one\n"
    "+two\n"
)


def init_repo(path: Path):
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "T21 Test"],
        cwd=path,
        check=True,
    )


def initial_commit(path: Path):
    (path / "file.txt").write_text(
        "one\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "file.txt"],
        cwd=path,
        check=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


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


def make_request(
    path: Path,
    operation: GitOperation,
    repair_fingerprint: str = "a" * 64,
    transaction_id: str = "tx-001",
) -> GitTransactionRequest:
    snapshot = GitReader(path).snapshot()

    return GitTransactionRequest(
        operation=operation,
        repository_root=str(path),
        expected_branch=snapshot.branch,
        expected_head_sha=snapshot.head_sha,
        transaction_id=transaction_id,
        repair_id="repair-001",
        repair_fingerprint=repair_fingerprint,
        changed_paths=("file.txt",),
        commit_message="test: verified repair",
        authorization_fingerprint="b" * 64,
        authorization_nonce="nonce-001",
    )


def make_verified_repair(path: Path) -> RepairResult:
    baseline = tree_fingerprint(path)
    file = path / "file.txt"

    # Compute expected patched tree without changing the Git baseline.
    file.write_text("two\n", encoding="utf-8")
    final_tree = tree_fingerprint(path)
    file.write_text("one\n", encoding="utf-8")

    patch_hash = patch_fingerprint(PATCH)

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
        patch_fingerprint=patch_hash,
        final_tree_fingerprint=final_tree,
        evidence=evidence,
        reason=RepairReason.VALID,
    )

    return RepairResult(
        schema_version="1.0",
        decision=RepairDecision.VERIFIED,
        reason=RepairReason.VALID,
        repair_id="repair-001",
        authorization_fingerprint="b" * 64,
        diagnosis_fingerprint="c" * 64,
        baseline_fingerprint=baseline,
        patch_fingerprint=patch_hash,
        final_tree_fingerprint=final_tree,
        changed_paths=("file.txt",),
        attempt=1,
        verification=verification,
        evidence_fingerprint=evidence.evidence_fingerprint,
        candidate_patch=PATCH,
    )


def test_dirty_tree_is_blocked(tmp_path: Path):
    init_repo(tmp_path)
    initial_commit(tmp_path)

    (tmp_path / "file.txt").write_text(
        "unexpected\n",
        encoding="utf-8",
    )

    request = make_request(
        tmp_path,
        GitOperation.COMMIT,
    )

    result = execute_git_transaction(
        request=request,
        authorization=None,
    )

    assert result.decision.value == "BLOCKED"
    assert result.reason.value == "DIRTY_WORKTREE"


def test_clean_repair_write_requires_t20_verified_result(
    tmp_path: Path,
):
    init_repo(tmp_path)
    initial_commit(tmp_path)

    request = make_request(
        tmp_path,
        GitOperation.COMMIT,
    )

    result = execute_git_transaction(
        request=request,
        authorization=make_authorization(),
        repair_result=None,
    )

    assert result.decision.value == "BLOCKED"
    assert result.reason.value == "REPAIR_NOT_VERIFIED"
    assert (tmp_path / "file.txt").read_text(
        encoding="utf-8"
    ) == "one\n"


def test_verified_patch_can_be_staged_then_committed(
    tmp_path: Path,
):
    init_repo(tmp_path)
    initial_commit(tmp_path)

    authorization = make_authorization()
    repair_result = make_verified_repair(tmp_path)
    patch_hash = repair_result.patch_fingerprint

    stage_request = make_request(
        tmp_path,
        GitOperation.STAGE,
        repair_fingerprint=patch_hash,
        transaction_id="tx-stage",
    )

    stage_result = execute_git_transaction(
        request=stage_request,
        authorization=authorization,
        repair_result=repair_result,
    )

    assert stage_result.decision.value == "READY_TO_WRITE"
    assert staged_paths(
        GitReader(tmp_path).repository
    ) == ("file.txt",)

    # Staging applies the source change but does not make a commit.
    assert (tmp_path / "file.txt").read_text(
        encoding="utf-8"
    ) == "two\n"

    commit_request = make_request(
        tmp_path,
        GitOperation.COMMIT,
        repair_fingerprint=patch_hash,
        transaction_id="tx-commit",
    )

    commit_result = execute_git_transaction(
        request=commit_request,
        authorization=authorization,
        repair_result=repair_result,
    )

    assert commit_result.decision.value == "COMMITTED"
    assert commit_result.commit_sha
    assert GitReader(tmp_path).snapshot().working_tree_clean
    assert (tmp_path / "file.txt").read_text(
        encoding="utf-8"
    ) == "two\n"


def test_t21_lock_does_not_make_clean_tree_dirty(
    tmp_path: Path,
):
    init_repo(tmp_path)
    initial_commit(tmp_path)

    reader = GitReader(tmp_path)
    assert reader.snapshot().working_tree_clean

    lock = GitTransactionLock(tmp_path)
    lock.acquire()

    try:
        assert reader.snapshot().working_tree_clean
    finally:
        lock.release()
