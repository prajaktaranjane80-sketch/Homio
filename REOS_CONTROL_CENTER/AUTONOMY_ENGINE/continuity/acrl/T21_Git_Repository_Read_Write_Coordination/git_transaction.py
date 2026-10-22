from __future__ import annotations

import tempfile
from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.T20_Autonomous_Repair_Patch_Verification.patch_engine import (
    patch_fingerprint,
)
from AUTONOMY_ENGINE.continuity.acrl.T20_Autonomous_Repair_Patch_Verification.patch_verification import (
    tree_fingerprint,
)
from AUTONOMY_ENGINE.continuity.acrl.T20_Autonomous_Repair_Patch_Verification.repair_models import (
    PatchVerification,
    RepairDecision,
    RepairResult,
)
from AUTONOMY_ENGINE.continuity.acrl.T20_Autonomous_Repair_Patch_Verification.repair_scope import (
    patch_paths,
)

from .git_authorization import validate_write_authorization
from .git_commit import create_commit, verify_commit
from .git_identity import fingerprint
from .git_lock import GitTransactionLock, GitTransactionLockError
from .git_models import (
    GitDecision,
    GitOperation,
    GitPolicy,
    GitReason,
    GitTransactionRequest,
    GitTransactionResult,
)
from .git_policy import normalize_path
from .git_provenance import GitProvenance
from .git_read import GitReader
from .git_registry import GitRegistry
from .git_repository import GitRepository
from .git_scope import validate_write_scope
from .git_stage import stage_exact_paths, staged_paths
from .git_validation import validate_request


_REPAIR_OPERATIONS = {
    GitOperation.STAGE,
    GitOperation.COMMIT,
    GitOperation.PUSH,
}


def _result(
    *,
    request: GitTransactionRequest,
    decision: GitDecision,
    reason: GitReason,
    before,
    after,
    changed_paths=(),
    staged=(),
    commit_sha=None,
    push_performed=False,
    push_verified=False,
    explanation="",
) -> GitTransactionResult:
    payload = {
        "transaction_id": request.transaction_id,
        "repair_id": request.repair_id,
        "repair_fingerprint": request.repair_fingerprint,
        "before": before.fingerprint,
        "after": after.fingerprint,
        "commit_sha": commit_sha,
        "changed_paths": tuple(changed_paths),
        "staged_paths": tuple(staged),
        "push_performed": push_performed,
        "push_verified": push_verified,
        "decision": decision.value,
        "reason": reason.value,
    }

    return GitTransactionResult(
        schema_version="1.0",
        decision=decision,
        reason=reason,
        operation=request.operation,
        transaction_id=request.transaction_id,
        repair_id=request.repair_id,
        repair_fingerprint=request.repair_fingerprint,
        repository_root=request.repository_root,
        branch_before=before.branch,
        branch_after=after.branch,
        head_before=before.head_sha,
        head_after=after.head_sha,
        changed_paths=tuple(changed_paths),
        staged_paths=tuple(staged),
        commit_sha=commit_sha,
        remote_name=request.remote_name,
        push_performed=push_performed,
        push_verified=push_verified,
        before_fingerprint=before.fingerprint,
        after_fingerprint=after.fingerprint,
        transaction_fingerprint=fingerprint(payload),
        explanation=explanation,
    )


def _valid_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False

    return all(
        character in "0123456789abcdef"
        for character in value
    )


def _verified_patch(
    *,
    request: GitTransactionRequest,
    repair_result,
    scoped_paths: tuple[str, ...],
) -> str:
    if not isinstance(repair_result, RepairResult):
        raise ValueError(
            "T21 requires the actual T20 RepairResult type."
        )

    if repair_result.decision is not RepairDecision.VERIFIED:
        raise ValueError(
            "T20 result decision is not VERIFIED."
        )

    verification = repair_result.verification

    if (
        not isinstance(verification, PatchVerification)
        or verification.passed is not True
    ):
        raise ValueError(
            "T20 verification evidence is missing or unsuccessful."
        )

    patch = repair_result.candidate_patch

    if not isinstance(patch, str) or not patch:
        raise ValueError(
            "T20 VERIFIED result has no candidate patch."
        )

    if repair_result.repair_id != request.repair_id:
        raise ValueError(
            "T20 repair ID does not match the T21 request."
        )

    if (
        repair_result.authorization_fingerprint
        != request.authorization_fingerprint
    ):
        raise ValueError(
            "T20 and T21 authorization fingerprints do not match."
        )

    calculated_fingerprint = patch_fingerprint(patch)

    if (
        calculated_fingerprint != request.repair_fingerprint
        or repair_result.patch_fingerprint != calculated_fingerprint
        or verification.patch_fingerprint != calculated_fingerprint
    ):
        raise ValueError(
            "T20 patch fingerprint does not match the T21 request."
        )

    paths = tuple(sorted(patch_paths(patch)))

    result_paths = tuple(
        sorted(normalize_path(path) for path in repair_result.changed_paths)
    )

    verification_paths = tuple(
        sorted(normalize_path(path) for path in verification.changed_paths)
    )

    if (
        paths != scoped_paths
        or paths != result_paths
        or paths != verification_paths
    ):
        raise ValueError(
            "T20 patch paths, result paths, verification paths "
            "and T21 authorized scope differ."
        )

    if (
        not _valid_sha256(repair_result.baseline_fingerprint)
        or not _valid_sha256(repair_result.final_tree_fingerprint)
    ):
        raise ValueError(
            "T20 baseline or final tree fingerprint is invalid."
        )

    if (
        verification.final_tree_fingerprint
        != repair_result.final_tree_fingerprint
    ):
        raise ValueError(
            "T20 verification and repair result final-tree fingerprints differ."
        )

    return patch


def _apply_patch_text(
    repository: GitRepository,
    patch: str,
    *,
    check_only: bool = False,
    reverse: bool = False,
) -> None:
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            suffix=".patch",
            delete=False,
        ) as temporary:
            temporary.write(patch)
            temporary_path = Path(temporary.name)

        args = ["apply"]

        if check_only:
            args.append("--check")

        if reverse:
            args.append("--reverse")

        args.extend(
            [
                "--whitespace=nowarn",
                str(temporary_path),
            ]
        )

        completed = repository.run(
            *args,
            check=False,
        )

        if completed.returncode != 0:
            raise ValueError(
                completed.stderr.strip()
                or completed.stdout.strip()
                or "git apply failed."
            )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _rollback_patch(
    *,
    repository: GitRepository,
    reader: GitReader,
    patch: str,
    paths: tuple[str, ...],
    baseline_fingerprint: str,
    expected_head_sha: str,
) -> bool:
    """Restore the authorized patch only if the original HEAD is unchanged."""

    try:
        if reader.snapshot().head_sha != expected_head_sha:
            return False

        reset_result = repository.run(
            "reset",
            "--",
            *paths,
            check=False,
        )

        if reset_result.returncode != 0:
            return False

        _apply_patch_text(
            repository,
            patch,
            reverse=True,
        )

        after = reader.snapshot()

        return (
            after.head_sha == expected_head_sha
            and tree_fingerprint(repository.root) == baseline_fingerprint
            and after.working_tree_clean
        )
    except Exception:
        return False


def _is_staged_continuation(
    *,
    repository: GitRepository,
    snapshot,
    scoped_paths: tuple[str, ...],
    expected_final_tree: str,
) -> bool:
    lines = [
        line
        for line in snapshot.status_porcelain.splitlines()
        if line
    ]

    if not lines:
        return False

    allowed_index_status = {
        "A", "C", "D", "M", "R", "T", "U",
    }

    status_paths: set[str] = set()

    for line in lines:
        if len(line) < 4:
            return False

        index_status = line[0]
        worktree_status = line[1]

        if index_status not in allowed_index_status:
            return False

        if worktree_status != " ":
            return False

        status_paths.add(normalize_path(line[3:]))

    if status_paths != set(scoped_paths):
        return False

    if staged_paths(repository) != scoped_paths:
        return False

    if repository.run(
        "diff",
        "--name-only",
        "--no-renames",
    ).stdout.strip():
        return False

    return tree_fingerprint(repository.root) == expected_final_tree


def execute_git_transaction(
    *,
    request: GitTransactionRequest,
    policy: GitPolicy | None = None,
    authorization=None,
    repair_result=None,
) -> GitTransactionResult:
    policy = policy or GitPolicy()

    GitRegistry().validate()
    GitProvenance().validate()
    validate_request(request, policy)

    repository = GitRepository(request.repository_root)
    reader = GitReader(request.repository_root)
    before = reader.snapshot()

    if before.branch != request.expected_branch:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.BRANCH_MISMATCH,
            before=before,
            after=before,
            explanation="Repository branch does not match expected branch.",
        )

    if before.head_sha != request.expected_head_sha:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.HEAD_MISMATCH,
            before=before,
            after=before,
            explanation="Repository HEAD changed from expected baseline.",
        )

    if request.operation is GitOperation.READ:
        return _result(
            request=request,
            decision=GitDecision.READ_ONLY,
            reason=GitReason.VALID,
            before=before,
            after=before,
            explanation="Read-only Git inspection completed.",
        )

    if (
        not before.working_tree_clean
        and request.operation not in {
            GitOperation.COMMIT,
            GitOperation.PUSH,
        }
    ):
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.DIRTY_WORKTREE,
            before=before,
            after=before,
            explanation="Write transaction requires a clean working tree.",
        )

    if (
        not before.working_tree_clean
        and request.operation in {
            GitOperation.COMMIT,
            GitOperation.PUSH,
        }
        and repair_result is None
    ):
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.DIRTY_WORKTREE,
            before=before,
            after=before,
            explanation="Dirty tree has no T20 handoff for continuation.",
        )

    if authorization is None:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.AUTHORIZATION_REQUIRED,
            before=before,
            after=before,
            explanation="T18 authorization is required.",
        )

    try:
        validate_write_authorization(authorization, request)
    except Exception as exc:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.AUTHORIZATION_INVALID,
            before=before,
            after=before,
            explanation=str(exc),
        )

    try:
        scoped_paths = validate_write_scope(request, policy)
    except Exception as exc:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.UNAUTHORIZED_PATH,
            before=before,
            after=before,
            explanation=str(exc),
        )

    patch = ""
    expected_baseline = ""
    expected_final_tree = ""
    staged_continuation = False

    if request.operation in _REPAIR_OPERATIONS:
        if repair_result is None:
            return _result(
                request=request,
                decision=GitDecision.BLOCKED,
                reason=GitReason.REPAIR_NOT_VERIFIED,
                before=before,
                after=before,
                explanation="T21 STAGE/COMMIT/PUSH requires a T20 VERIFIED result.",
            )

        try:
            patch = _verified_patch(
                request=request,
                repair_result=repair_result,
                scoped_paths=scoped_paths,
            )
        except Exception as exc:
            return _result(
                request=request,
                decision=GitDecision.BLOCKED,
                reason=GitReason.UNEXPECTED_CHANGE,
                before=before,
                after=before,
                explanation=str(exc),
            )

        expected_baseline = repair_result.baseline_fingerprint
        expected_final_tree = repair_result.final_tree_fingerprint

        if before.working_tree_clean:
            if tree_fingerprint(repository.root) != expected_baseline:
                return _result(
                    request=request,
                    decision=GitDecision.BLOCKED,
                    reason=GitReason.BASELINE_DRIFT,
                    before=before,
                    after=before,
                    explanation="Live tree fingerprint does not match the T20 baseline.",
                )
        else:
            staged_continuation = (
                request.operation in {
                    GitOperation.COMMIT,
                    GitOperation.PUSH,
                }
                and _is_staged_continuation(
                    repository=repository,
                    snapshot=before,
                    scoped_paths=scoped_paths,
                    expected_final_tree=expected_final_tree,
                )
            )

            if not staged_continuation:
                return _result(
                    request=request,
                    decision=GitDecision.BLOCKED,
                    reason=GitReason.DIRTY_WORKTREE,
                    before=before,
                    after=before,
                    explanation=(
                        "Dirty worktree is not an exact T20-verified "
                        "staged continuation."
                    ),
                )
    elif not before.working_tree_clean:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.DIRTY_WORKTREE,
            before=before,
            after=before,
            explanation="Branch operation requires a clean working tree.",
        )

    try:
        with GitTransactionLock(request.repository_root):
            current = reader.snapshot()

            if current.fingerprint != before.fingerprint:
                after = reader.snapshot()
                return _result(
                    request=request,
                    decision=GitDecision.BLOCKED,
                    reason=GitReason.CONCURRENT_TRANSACTION,
                    before=before,
                    after=after,
                    explanation=(
                        "Repository snapshot changed before the lock was acquired."
                    ),
                )

            # All policy, commit-message and remote checks occur before
            # patch application, staging, or commit creation.
            if request.operation in _REPAIR_OPERATIONS:
                if not policy.allow_staging:
                    return _result(
                        request=request,
                        decision=GitDecision.BLOCKED,
                        reason=GitReason.STAGE_MISMATCH,
                        before=before,
                        after=current,
                        changed_paths=scoped_paths,
                        explanation="Staging is disabled by T21 policy.",
                    )

                if request.operation in {
                    GitOperation.COMMIT,
                    GitOperation.PUSH,
                }:
                    if not policy.allow_commit:
                        return _result(
                            request=request,
                            decision=GitDecision.BLOCKED,
                            reason=GitReason.COMMIT_FAILURE,
                            before=before,
                            after=current,
                            changed_paths=scoped_paths,
                            explanation="Commit is disabled by T21 policy.",
                        )

                    if not request.commit_message.strip():
                        return _result(
                            request=request,
                            decision=GitDecision.REJECTED,
                            reason=GitReason.EMPTY_COMMIT,
                            before=before,
                            after=current,
                            changed_paths=scoped_paths,
                            explanation="A non-empty commit message is required.",
                        )

                if request.operation is GitOperation.PUSH:
                    if not policy.allow_push:
                        return _result(
                            request=request,
                            decision=GitDecision.BLOCKED,
                            reason=GitReason.PUSH_REJECTED,
                            before=before,
                            after=current,
                            changed_paths=scoped_paths,
                            explanation="Git push is disabled by policy.",
                        )

                    if (
                        not request.remote_name
                        or request.remote_name not in repository.remote_names()
                    ):
                        return _result(
                            request=request,
                            decision=GitDecision.BLOCKED,
                            reason=GitReason.REMOTE_UNAVAILABLE,
                            before=before,
                            after=current,
                            changed_paths=scoped_paths,
                            explanation="Requested remote is unavailable.",
                        )

            if request.operation is GitOperation.CREATE_BRANCH:
                target = (request.target_branch or "").strip()

                if not target:
                    return _result(
                        request=request,
                        decision=GitDecision.REJECTED,
                        reason=GitReason.BRANCH_MISMATCH,
                        before=before,
                        after=current,
                        explanation="Target branch is required.",
                    )

                repository.run("switch", "-c", target)
                after = reader.snapshot()

                return _result(
                    request=request,
                    decision=GitDecision.READY_TO_WRITE,
                    reason=GitReason.VALID,
                    before=before,
                    after=after,
                    changed_paths=scoped_paths,
                    explanation="Authorized branch created.",
                )

            if request.operation in _REPAIR_OPERATIONS:
                patch_applied = False

                if not staged_continuation:
                    if tree_fingerprint(repository.root) != expected_baseline:
                        after = reader.snapshot()
                        return _result(
                            request=request,
                            decision=GitDecision.BLOCKED,
                            reason=GitReason.BASELINE_DRIFT,
                            before=before,
                            after=after,
                            explanation=(
                                "Tree changed while waiting for the transaction lock."
                            ),
                        )

                    try:
                        _apply_patch_text(
                            repository,
                            patch,
                            check_only=True,
                        )
                        _apply_patch_text(repository, patch)
                        patch_applied = True

                        if tree_fingerprint(repository.root) != expected_final_tree:
                            rollback_ok = _rollback_patch(
                                repository=repository,
                                reader=reader,
                                patch=patch,
                                paths=scoped_paths,
                                baseline_fingerprint=expected_baseline,
                                expected_head_sha=before.head_sha,
                            )
                            after = reader.snapshot()

                            return _result(
                                request=request,
                                decision=(
                                    GitDecision.BLOCKED
                                    if rollback_ok
                                    else GitDecision.FAIL_CLOSED
                                ),
                                reason=GitReason.UNEXPECTED_CHANGE,
                                before=before,
                                after=after,
                                changed_paths=scoped_paths,
                                explanation=(
                                    "Live final tree differs from T20. "
                                    + (
                                        "Patch was rolled back."
                                        if rollback_ok
                                        else "Rollback could not be verified."
                                    )
                                ),
                            )

                        stage_exact_paths(repository, scoped_paths, policy)
                        staged = staged_paths(repository)

                        if staged != scoped_paths:
                            rollback_ok = _rollback_patch(
                                repository=repository,
                                reader=reader,
                                patch=patch,
                                paths=scoped_paths,
                                baseline_fingerprint=expected_baseline,
                                expected_head_sha=before.head_sha,
                            )
                            after = reader.snapshot()

                            return _result(
                                request=request,
                                decision=(
                                    GitDecision.BLOCKED
                                    if rollback_ok
                                    else GitDecision.FAIL_CLOSED
                                ),
                                reason=GitReason.STAGE_MISMATCH,
                                before=before,
                                after=after,
                                changed_paths=scoped_paths,
                                staged=staged,
                                explanation=(
                                    "Staged path set does not match the authorized "
                                    "patch paths. "
                                    + (
                                        "Patch was rolled back."
                                        if rollback_ok
                                        else "Rollback could not be verified."
                                    )
                                ),
                            )
                    except Exception as exc:
                        rollback_ok = (
                            _rollback_patch(
                                repository=repository,
                                reader=reader,
                                patch=patch,
                                paths=scoped_paths,
                                baseline_fingerprint=expected_baseline,
                                expected_head_sha=before.head_sha,
                            )
                            if patch_applied
                            else False
                        )
                        after = reader.snapshot()

                        return _result(
                            request=request,
                            decision=(
                                GitDecision.BLOCKED
                                if not patch_applied or rollback_ok
                                else GitDecision.FAIL_CLOSED
                            ),
                            reason=GitReason.UNEXPECTED_CHANGE,
                            before=before,
                            after=after,
                            changed_paths=scoped_paths,
                            staged=staged_paths(repository),
                            explanation=(
                                f"Patch application or staging failed: {exc}. "
                                + (
                                    "Rollback was verified."
                                    if patch_applied and rollback_ok
                                    else (
                                        "Rollback was not verified."
                                        if patch_applied
                                        else "No patch application was completed."
                                    )
                                )
                            ),
                        )
                else:
                    if (
                        tree_fingerprint(repository.root) != expected_final_tree
                        or staged_paths(repository) != scoped_paths
                    ):
                        after = reader.snapshot()
                        return _result(
                            request=request,
                            decision=GitDecision.BLOCKED,
                            reason=GitReason.STAGE_MISMATCH,
                            before=before,
                            after=after,
                            changed_paths=scoped_paths,
                            staged=staged_paths(repository),
                            explanation=(
                                "Staged continuation no longer matches T20's verified tree."
                            ),
                        )

                staged = staged_paths(repository)

                if request.operation is GitOperation.STAGE:
                    after = reader.snapshot()
                    return _result(
                        request=request,
                        decision=GitDecision.READY_TO_WRITE,
                        reason=GitReason.VALID,
                        before=before,
                        after=after,
                        changed_paths=scoped_paths,
                        staged=staged,
                        explanation=(
                            "T20 patch revalidated, applied and staged exactly; "
                            "no commit created."
                        ),
                    )

                try:
                    commit_sha = create_commit(
                        repository,
                        request.commit_message,
                        policy,
                    )
                except ValueError as exc:
                    rollback_ok = _rollback_patch(
                        repository=repository,
                        reader=reader,
                        patch=patch,
                        paths=scoped_paths,
                        baseline_fingerprint=expected_baseline,
                        expected_head_sha=before.head_sha,
                    )
                    after = reader.snapshot()

                    return _result(
                        request=request,
                        decision=(
                            GitDecision.BLOCKED
                            if rollback_ok
                            else GitDecision.FAIL_CLOSED
                        ),
                        reason=GitReason.EMPTY_COMMIT,
                        before=before,
                        after=after,
                        changed_paths=scoped_paths,
                        staged=staged_paths(repository),
                        explanation=(
                            f"Commit was rejected: {exc}. "
                            + (
                                "Rollback was verified."
                                if rollback_ok
                                else (
                                    "Rollback could not be verified; "
                                    "transaction failed closed."
                                )
                            )
                        ),
                    )
                except Exception as exc:
                    rollback_ok = _rollback_patch(
                        repository=repository,
                        reader=reader,
                        patch=patch,
                        paths=scoped_paths,
                        baseline_fingerprint=expected_baseline,
                        expected_head_sha=before.head_sha,
                    )
                    after = reader.snapshot()

                    return _result(
                        request=request,
                        decision=(
                            GitDecision.BLOCKED
                            if rollback_ok
                            else GitDecision.FAIL_CLOSED
                        ),
                        reason=GitReason.COMMIT_FAILURE,
                        before=before,
                        after=after,
                        changed_paths=scoped_paths,
                        staged=staged_paths(repository),
                        explanation=(
                            f"Commit failed: {exc}. "
                            + (
                                "Rollback was verified."
                                if rollback_ok
                                else (
                                    "Rollback could not be verified; "
                                    "transaction failed closed."
                                )
                            )
                        ),
                    )

                if not verify_commit(repository, commit_sha):
                    after = reader.snapshot()
                    return _result(
                        request=request,
                        decision=GitDecision.FAIL_CLOSED,
                        reason=GitReason.COMMIT_VERIFICATION_FAILURE,
                        before=before,
                        after=after,
                        changed_paths=scoped_paths,
                        staged=staged,
                        commit_sha=commit_sha,
                        explanation="Commit could not be independently verified.",
                    )

                after = reader.snapshot()
                push_performed = False
                push_verified = False
                decision = GitDecision.COMMITTED
                reason = GitReason.VALID
                explanation = "Verified Git commit created."

                if request.operation is GitOperation.PUSH:
                    # Import before the try so the exception handler itself
                    # cannot fail because the classifier was never bound.
                    from .git_push import (
                        classify_git_push_error,
                        push_branch,
                        verify_remote_branch,
                    )

                    target_branch = request.target_branch or after.branch

                    try:
                        push_branch(
                            repository,
                            remote=request.remote_name,
                            branch=target_branch,
                            policy=policy,
                        )

                        push_performed = True

                        remote_sha = verify_remote_branch(
                            repository,
                            remote=request.remote_name,
                            branch=target_branch,
                        )

                        push_verified = remote_sha == commit_sha

                        if push_verified:
                            decision = GitDecision.PUSHED
                            explanation = (
                                "Commit created and remote branch independently verified."
                            )
                        else:
                            decision = GitDecision.FAIL_CLOSED
                            reason = GitReason.NON_FAST_FORWARD
                            explanation = (
                                "Remote branch did not resolve to the verified commit."
                            )

                    except Exception as exc:
                        reason, safe_explanation = classify_git_push_error(exc)

                        # The push may have reached the remote even if the
                        # client observed a timeout or server-side error.
                        # Never retry blindly: read back the exact branch.
                        try:
                            remote_sha = verify_remote_branch(
                                repository,
                                remote=request.remote_name,
                                branch=target_branch,
                            )
                        except Exception:
                            remote_sha = None

                        # Only the exact expected commit proves success.
                        if remote_sha == commit_sha:
                            return _result(
                                request=request,
                                decision=GitDecision.PUSHED,
                                reason=GitReason.VALID,
                                before=before,
                                after=reader.snapshot(),
                                changed_paths=scoped_paths,
                                staged=staged,
                                commit_sha=commit_sha,
                                push_performed=True,
                                push_verified=True,
                                explanation=(
                                    "Push returned an error, but independent remote "
                                    "readback confirms the exact expected commit."
                                ),
                            )

                        if (
                            remote_sha is not None
                            and reason in {
                                GitReason.NETWORK_FAILURE,
                                GitReason.RATE_LIMITED,
                                GitReason.NON_FAST_FORWARD,
                                GitReason.PUSH_REJECTED,
                            }
                        ):
                            reason = GitReason.NON_FAST_FORWARD
                            safe_explanation = (
                                "Remote readback returned a different commit. "
                                "Reconcile the current remote branch before any retry."
                            )
                        else:
                            safe_explanation = (
                                f"{safe_explanation} "
                                "The expected remote commit was not verified by readback; "
                                "no automatic retry was attempted."
                            )

                        return _result(
                            request=request,
                            decision=GitDecision.REJECTED,
                            reason=reason,
                            before=before,
                            after=reader.snapshot(),
                            changed_paths=scoped_paths,
                            staged=staged,
                            commit_sha=commit_sha,
                            push_performed=True,
                            push_verified=False,
                            explanation=safe_explanation,
                        )

    except GitTransactionLockError as exc:
        after = reader.snapshot()
        return _result(
            request=request,
            decision=GitDecision.FAIL_CLOSED,
            reason=GitReason.CONCURRENT_TRANSACTION,
            before=before,
            after=after,
            changed_paths=scoped_paths,
            explanation=(
                "T21 lock acquisition or release reported an ownership error: "
                f"{exc}. Inspect the returned HEAD and repository status."
            ),
        )

    return _result(
        request=request,
        decision=GitDecision.REJECTED,
        reason=GitReason.UNEXPECTED_CHANGE,
        before=before,
        after=reader.snapshot(),
        explanation="Unsupported T21 Git operation.",
    )
