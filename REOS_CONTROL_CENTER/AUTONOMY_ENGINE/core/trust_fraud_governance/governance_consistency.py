from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
import hashlib
import json


GOVERNANCE_CONSISTENCY_SCHEMA_VERSION = 1


class GovernanceConsistencyError(ValueError):
    """Base consistency error."""


class GovernanceStalePolicyError(
    GovernanceConsistencyError
):
    """Policy version/fingerprint is stale."""


class GovernanceStaleEvaluationError(
    GovernanceConsistencyError
):
    """Evaluation revision is stale."""


class GovernanceVersionConflictError(
    GovernanceConsistencyError
):
    """Version identity conflict."""


class GovernanceReplayConflictError(
    GovernanceConsistencyError
):
    """Replay content conflicts with recorded identity."""


class GovernanceDuplicateSignalError(
    GovernanceConsistencyError
):
    """Duplicate signal identity with conflicting content."""


class GovernanceDuplicateCommandError(
    GovernanceConsistencyError
):
    """Duplicate command identity with conflicting content."""


class GovernanceConcurrentReviewError(
    GovernanceConsistencyError
):
    """Concurrent review revision conflict."""


class ConsistencyCheck(str, Enum):
    POLICY_VERSION = "POLICY_VERSION"
    POLICY_FINGERPRINT = "POLICY_FINGERPRINT"
    EVALUATION_REVISION = "EVALUATION_REVISION"
    DECISION_FINGERPRINT = "DECISION_FINGERPRINT"
    SIGNAL_IDENTITY = "SIGNAL_IDENTITY"
    COMMAND_IDENTITY = "COMMAND_IDENTITY"
    REVIEW_REVISION = "REVIEW_REVISION"
    IDEMPOTENCY = "IDEMPOTENCY"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceConsistencyError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class GovernanceVersionToken:
    resource_type: str
    resource_id: str
    version: str
    fingerprint: str
    revision: int

    def __post_init__(self) -> None:
        for name in (
            "resource_type",
            "resource_id",
            "version",
            "fingerprint",
        ):
            object.__setattr__(
                self,
                name,
                _text(
                    getattr(self, name),
                    name,
                ),
            )

        if (
            isinstance(
                self.revision,
                bool,
            )
            or not isinstance(
                self.revision,
                int,
            )
            or self.revision < 0
        ):
            raise GovernanceConsistencyError(
                "revision must be integer >= 0."
            )

    @property
    def identity_key(
        self,
    ) -> tuple[str, str]:
        return (
            self.resource_type,
            self.resource_id,
        )


@dataclass(frozen=True, slots=True)
class GovernanceConsistencySnapshot:
    policy_id: str
    policy_version: str
    policy_fingerprint: str

    evaluation_id: str
    evaluation_revision: int

    decision_fingerprint: str | None = None

    schema_version: int = (
        GOVERNANCE_CONSISTENCY_SCHEMA_VERSION
    )

    review_id: str | None = None
    review_revision: int | None = None

    signal_identity: str | None = None
    signal_fingerprint: str | None = None

    command_identity: str | None = None
    command_fingerprint: str | None = None

    idempotency_key: str | None = None

    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "policy_id": self.policy_id,
                "policy_version": (
                    self.policy_version
                ),
                "policy_fingerprint": (
                    self.policy_fingerprint
                ),
                "evaluation_id": (
                    self.evaluation_id
                ),
                "evaluation_revision": (
                    self.evaluation_revision
                ),
                "decision_fingerprint": (
                    self.decision_fingerprint
                ),
                "review_id": self.review_id,
                "review_revision": (
                    self.review_revision
                ),
                "signal_identity": (
                    self.signal_identity
                ),
                "signal_fingerprint": (
                    self.signal_fingerprint
                ),
                "command_identity": (
                    self.command_identity
                ),
                "command_fingerprint": (
                    self.command_fingerprint
                ),
                "idempotency_key": (
                    self.idempotency_key
                ),
                "schema_version": (
                    self.schema_version
                ),
            }
        )


class GovernanceConsistencyGuard:
    """Stateless deterministic consistency guards."""

    @staticmethod
    def assert_policy_current(
        *,
        expected_policy_version: str,
        expected_policy_fingerprint: str,
        actual_policy_version: str,
        actual_policy_fingerprint: str,
    ) -> None:
        if (
            expected_policy_version
            != actual_policy_version
        ):
            raise GovernanceStalePolicyError(
                "Governance policy version is stale."
            )

        if (
            expected_policy_fingerprint
            != actual_policy_fingerprint
        ):
            raise GovernanceStalePolicyError(
                "Governance policy fingerprint is stale."
            )

    @staticmethod
    def assert_revision_current(
        *,
        expected_revision: int,
        actual_revision: int,
    ) -> None:
        if expected_revision != actual_revision:
            raise GovernanceStaleEvaluationError(
                "Governance evaluation revision is stale."
            )

    @staticmethod
    def assert_concurrent_review_safe(
        *,
        expected_review_revision: int,
        actual_review_revision: int,
    ) -> None:
        if (
            expected_review_revision
            != actual_review_revision
        ):
            raise GovernanceConcurrentReviewError(
                "Concurrent governance review detected."
            )

    @staticmethod
    def assert_identity_compatible(
        *,
        expected_resource_type: str,
        expected_resource_id: str,
        actual_resource_type: str,
        actual_resource_id: str,
    ) -> None:
        if (
            expected_resource_type
            != actual_resource_type
            or expected_resource_id
            != actual_resource_id
        ):
            raise GovernanceVersionConflictError(
                "Governance resource identities differ."
            )

    @staticmethod
    def assert_replay_safe(
        *,
        recorded_fingerprint: str,
        replayed_fingerprint: str,
    ) -> None:
        if (
            recorded_fingerprint
            != replayed_fingerprint
        ):
            raise GovernanceReplayConflictError(
                "Replay material conflicts with "
                "recorded identity."
            )

    @staticmethod
    def assert_duplicate_signal_safe(
        *,
        signal_identity: str,
        existing_fingerprint: str | None,
        incoming_fingerprint: str,
    ) -> None:
        _text(
            signal_identity,
            "signal_identity",
        )

        if (
            existing_fingerprint is not None
            and existing_fingerprint
            != incoming_fingerprint
        ):
            raise GovernanceDuplicateSignalError(
                "Duplicate signal identity contains "
                "conflicting content."
            )

    @staticmethod
    def assert_duplicate_command_safe(
        *,
        command_identity: str,
        existing_fingerprint: str | None,
        incoming_fingerprint: str,
    ) -> None:
        _text(
            command_identity,
            "command_identity",
        )

        if (
            existing_fingerprint is not None
            and existing_fingerprint
            != incoming_fingerprint
        ):
            raise GovernanceDuplicateCommandError(
                "Duplicate command identity contains "
                "conflicting content."
            )

    @staticmethod
    def idempotency_key(
        *,
        tenant_id: str,
        command_identity: str,
        command_fingerprint: str,
    ) -> str:
        return _fingerprint(
            {
                "tenant_id": _text(
                    tenant_id,
                    "tenant_id",
                ),
                "command_identity": _text(
                    command_identity,
                    "command_identity",
                ),
                "command_fingerprint": _text(
                    command_fingerprint,
                    "command_fingerprint",
                ),
            }
        )

    @staticmethod
    def assert_idempotent(
        *,
        expected_idempotency_key: str,
        actual_idempotency_key: str,
    ) -> None:
        if (
            expected_idempotency_key
            != actual_idempotency_key
        ):
            raise GovernanceVersionConflictError(
                "Idempotency key mismatch."
            )

    @staticmethod
    def build_token(
        *,
        resource_type: str,
        resource_id: str,
        version: str,
        fingerprint: str,
        revision: int,
    ) -> GovernanceVersionToken:
        return GovernanceVersionToken(
            resource_type=resource_type,
            resource_id=resource_id,
            version=version,
            fingerprint=fingerprint,
            revision=revision,
        )

    @staticmethod
    def build_snapshot(
        *,
        policy_id: str,
        policy_version: str,
        policy_fingerprint: str,
        evaluation_id: str,
        evaluation_revision: int,
        decision_fingerprint: str | None = None,
        review_id: str | None = None,
        review_revision: int | None = None,
        signal_identity: str | None = None,
        signal_fingerprint: str | None = None,
        command_identity: str | None = None,
        command_fingerprint: str | None = None,
        idempotency_key: str | None = None,
    ) -> GovernanceConsistencySnapshot:
        return GovernanceConsistencySnapshot(
            policy_id=policy_id,
            policy_version=policy_version,
            policy_fingerprint=policy_fingerprint,
            evaluation_id=evaluation_id,
            evaluation_revision=evaluation_revision,
            decision_fingerprint=decision_fingerprint,
            review_id=review_id,
            review_revision=review_revision,
            signal_identity=signal_identity,
            signal_fingerprint=signal_fingerprint,
            command_identity=command_identity,
            command_fingerprint=command_fingerprint,
            idempotency_key=idempotency_key,
        )


__all__ = [
    "GOVERNANCE_CONSISTENCY_SCHEMA_VERSION",
    "GovernanceConsistencyError",
    "GovernanceStalePolicyError",
    "GovernanceStaleEvaluationError",
    "GovernanceVersionConflictError",
    "GovernanceReplayConflictError",
    "GovernanceDuplicateSignalError",
    "GovernanceDuplicateCommandError",
    "GovernanceConcurrentReviewError",
    "ConsistencyCheck",
    "GovernanceVersionToken",
    "GovernanceConsistencySnapshot",
    "GovernanceConsistencyGuard",
]
