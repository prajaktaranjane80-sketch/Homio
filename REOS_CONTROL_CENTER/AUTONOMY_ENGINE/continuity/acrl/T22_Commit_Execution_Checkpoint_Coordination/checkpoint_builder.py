from __future__ import annotations

from .checkpoint_identity import fingerprint
from .checkpoint_models import (
    CheckpointRequest,
    ExecutionCheckpoint,
)


def build_checkpoint(
    request: CheckpointRequest,
) -> ExecutionCheckpoint:
    payload = {
        "schema_version": "1.0",
        "checkpoint_version": "1.0",
        "checkpoint_id": request.checkpoint_id,
        "kind": request.checkpoint_kind.value,
        "execution_intent": request.execution_intent,
        "transaction_id": request.transaction_id,
        "repair_id": request.repair_id,
        "repository_root": request.repository_root,
        "branch": request.expected_branch,
        "commit_sha": request.expected_commit_sha,
        "authorization_fingerprint": (
            request.authorization_fingerprint
        ),
        "authorization_nonce": request.authorization_nonce,
        "repair_fingerprint": request.repair_fingerprint,
        "transaction_fingerprint": (
            request.transaction_fingerprint
        ),
        "expected_branch": request.expected_branch,
        "expected_commit_sha": (
            request.expected_commit_sha
        ),
        "created_from_head": (
            request.expected_commit_sha
        ),
        "protected_state_fingerprint": (
            request.protected_state_fingerprint
        ),
    }

    checkpoint_fingerprint = fingerprint(
        payload
    )

    return ExecutionCheckpoint(
        schema_version="1.0",
        checkpoint_version="1.0",
        checkpoint_id=request.checkpoint_id,
        kind=request.checkpoint_kind,
        execution_intent=request.execution_intent,
        transaction_id=request.transaction_id,
        repair_id=request.repair_id,
        repository_root=request.repository_root,
        branch=request.expected_branch,
        commit_sha=request.expected_commit_sha,
        authorization_fingerprint=(
            request.authorization_fingerprint
        ),
        authorization_nonce=request.authorization_nonce,
        repair_fingerprint=request.repair_fingerprint,
        transaction_fingerprint=(
            request.transaction_fingerprint
        ),
        expected_branch=request.expected_branch,
        expected_commit_sha=(
            request.expected_commit_sha
        ),
        created_from_head=(
            request.expected_commit_sha
        ),
        protected_state_fingerprint=(
            request.protected_state_fingerprint
        ),
        checkpoint_fingerprint=(
            checkpoint_fingerprint
        ),
    )
