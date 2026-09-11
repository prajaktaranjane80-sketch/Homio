from __future__ import annotations

from .git_authorization import (
    validate_write_authorization,
)
from .git_commit import (
    create_commit,
    verify_commit,
)
from .git_identity import fingerprint
from .git_lock import GitTransactionLock
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
from .git_stage import (
    stage_exact_paths,
    staged_paths,
)
from .git_validation import validate_request


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
    validate_request(
        request,
        policy,
    )

    repository = GitRepository(
        request.repository_root
    )

    reader = GitReader(
        request.repository_root
    )

    before = reader.snapshot()

    if (
        before.branch
        != request.expected_branch
    ):
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.BRANCH_MISMATCH,
            before=before,
            after=before,
            explanation="Repository branch does not match expected branch.",
        )

    if (
        before.head_sha
        != request.expected_head_sha
    ):
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

    if not before.working_tree_clean:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.DIRTY_WORKTREE,
            before=before,
            after=before,
            explanation="Write transaction requires a clean working tree.",
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
        validate_write_authorization(
            authorization,
            request,
        )
    except Exception as exc:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.AUTHORIZATION_INVALID,
            before=before,
            after=before,
            explanation=str(exc),
        )

    if repair_result is not None:
        if getattr(
            repair_result,
            "decision",
            None,
        ).value != "VERIFIED":
            return _result(
                request=request,
                decision=GitDecision.BLOCKED,
                reason=GitReason.REPAIR_NOT_VERIFIED,
                before=before,
                after=before,
                explanation="T21 write requires T20 VERIFIED repair.",
            )

        if (
            getattr(
                repair_result,
                "patch_fingerprint",
                None,
            )
            != request.repair_fingerprint
        ):
            return _result(
                request=request,
                decision=GitDecision.BLOCKED,
                reason=GitReason.UNEXPECTED_CHANGE,
                before=before,
                after=before,
                explanation="T20 repair fingerprint mismatch.",
            )

    try:
        scoped_paths = validate_write_scope(
            request,
            policy,
        )
    except Exception as exc:
        return _result(
            request=request,
            decision=GitDecision.BLOCKED,
            reason=GitReason.UNAUTHORIZED_PATH,
            before=before,
            after=before,
            explanation=str(exc),
        )

    with GitTransactionLock(
        request.repository_root
    ):
        current = reader.snapshot()

        if current.head_sha != before.head_sha:
            return _result(
                request=request,
                decision=GitDecision.BLOCKED,
                reason=GitReason.CONCURRENT_TRANSACTION,
                before=before,
                after=current,
                explanation="Repository changed before transaction lock execution.",
            )

        if request.operation is GitOperation.CREATE_BRANCH:
            target = (
                request.target_branch
                or ""
            ).strip()

            if not target:
                return _result(
                    request=request,
                    decision=GitDecision.REJECTED,
                    reason=GitReason.BRANCH_MISMATCH,
                    before=before,
                    after=current,
                    explanation="Target branch is required.",
                )

            repository.run(
                "switch",
                "-c",
                target,
            )

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

        if request.operation in {
            GitOperation.STAGE,
            GitOperation.COMMIT,
            GitOperation.PUSH,
        }:
            stage_exact_paths(
                repository,
                scoped_paths,
                policy,
            )

            staged = staged_paths(
                repository
            )

            if staged != scoped_paths:
                repository.run(
                    "reset",
                    "--",
                    *staged,
                    check=False,
                )

                after = reader.snapshot()

                return _result(
                    request=request,
                    decision=GitDecision.BLOCKED,
                    reason=GitReason.STAGE_MISMATCH,
                    before=before,
                    after=after,
                    changed_paths=scoped_paths,
                    staged=staged,
                    explanation="Staged path set does not match authorized scope.",
                )

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
                    explanation="Authorized files staged.",
                )

            try:
                commit_sha = create_commit(
                    repository,
                    request.commit_message,
                    policy,
                )
            except ValueError as exc:
                after = reader.snapshot()

                return _result(
                    request=request,
                    decision=GitDecision.REJECTED,
                    reason=GitReason.EMPTY_COMMIT,
                    before=before,
                    after=after,
                    changed_paths=scoped_paths,
                    staged=staged,
                    explanation=str(exc),
                )
            except Exception as exc:
                after = reader.snapshot()

                return _result(
                    request=request,
                    decision=GitDecision.REJECTED,
                    reason=GitReason.COMMIT_FAILURE,
                    before=before,
                    after=after,
                    changed_paths=scoped_paths,
                    staged=staged,
                    explanation=str(exc),
                )

            if not verify_commit(
                repository,
                commit_sha,
            ):
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

            if request.push:
                if not request.remote_name:
                    return _result(
                        request=request,
                        decision=GitDecision.BLOCKED,
                        reason=GitReason.REMOTE_UNAVAILABLE,
                        before=before,
                        after=after,
                        changed_paths=scoped_paths,
                        staged=staged,
                        commit_sha=commit_sha,
                        explanation="Remote name is required for push.",
                    )

                if request.remote_name not in (
                    repository.remote_names()
                ):
                    return _result(
                        request=request,
                        decision=GitDecision.BLOCKED,
                        reason=GitReason.REMOTE_UNAVAILABLE,
                        before=before,
                        after=after,
                        changed_paths=scoped_paths,
                        staged=staged,
                        commit_sha=commit_sha,
                        explanation="Requested remote is unavailable.",
                    )

                try:
                    from .git_push import (
                        push_branch,
                        verify_remote_branch,
                    )

                    push_branch(
                        repository,
                        remote=request.remote_name,
                        branch=(
                            request.target_branch
                            or after.branch
                        ),
                        policy=policy,
                    )

                    remote_sha = verify_remote_branch(
                        repository,
                        remote=request.remote_name,
                        branch=(
                            request.target_branch
                            or after.branch
                        ),
                    )

                    push_performed = True
                    push_verified = (
                        remote_sha == commit_sha
                    )

                    if not push_verified:
                        decision = GitDecision.FAIL_CLOSED
                        reason = (
                            GitReason.NON_FAST_FORWARD
                        )
                        explanation = (
                            "Remote branch did not resolve to "
                            "the created commit."
                        )
                    else:
                        decision = GitDecision.PUSHED
                        explanation = (
                            "Commit created and remote push independently verified."
                        )

                except Exception as exc:
                    return _result(
                        request=request,
                        decision=GitDecision.REJECTED,
                        reason=GitReason.PUSH_REJECTED,
                        before=before,
                        after=reader.snapshot(),
                        changed_paths=scoped_paths,
                        staged=staged,
                        commit_sha=commit_sha,
                        push_performed=True,
                        push_verified=False,
                        explanation=str(exc),
                    )

            final = reader.snapshot()

            return _result(
                request=request,
                decision=decision,
                reason=reason,
                before=before,
                after=final,
                changed_paths=scoped_paths,
                staged=staged,
                commit_sha=commit_sha,
                push_performed=push_performed,
                push_verified=push_verified,
                explanation=explanation,
            )

    return _result(
        request=request,
        decision=GitDecision.REJECTED,
        reason=GitReason.UNEXPECTED_CHANGE,
        before=before,
        after=before,
        explanation="Unsupported T21 Git operation.",
    )
