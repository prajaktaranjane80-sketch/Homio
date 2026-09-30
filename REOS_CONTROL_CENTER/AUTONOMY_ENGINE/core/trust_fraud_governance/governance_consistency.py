"""CORE-007 — Governance Consistency & Concurrency Boundary.

Protects governance evaluation from:
- stale policy versions,
- stale evaluation results,
- conflicting fingerprints,
- duplicate governance identities,
- replay of obsolete decision material.

This module does NOT own persistence or distributed locking.
The caller supplies the authoritative revision/version values.
"""

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
    """Policy version is stale."""


class GovernanceStaleEvaluationError(
    GovernanceConsistencyError
):
    """Evaluation revision is stale."""


class GovernanceVersionConflictError(
    GovernanceConsistencyError
):
    """Same identity contains different material."""


class GovernanceReplayConflictError(
    GovernanceConsistencyError
):
    """Replay material conflicts with recorded identity."""


class ConsistencyCheck(str, Enum):
    POLICY_VERSION = "POLICY_VERSION"
    POLICY_FINGERPRINT = "POLICY_FINGERPRINT"
    EVALUATION_REVISION = "EVALUATION_REVISION"
    DECISION_FINGERPRINT = "DECISION_FINGERPRINT"


@dataclass(frozen=True, slots=True)
class GovernanceVersionToken:
    """Immutable optimistic-concurrency token."""

    resource_type: str
    resource_id: str
    version: str
    fingerprint: str
    revision: int

    def __post_init__(self) -> None:
        if not self.resource_type.strip():
            raise GovernanceConsistencyError(
                "resource_type is required."
            )

        if not self.resource_id.strip():
            raise GovernanceConsistencyError(
                "resource_id is required."
            )

        if not self.version.strip():
            raise GovernanceConsistencyError(
                "version is required."
            )

        if not self.fingerprint.strip():
            raise GovernanceConsistencyError(
                "fingerprint is required."
            )

        if (
            isinstance(self.revision, bool)
            or not isinstance(self.revision, int)
            or self.revision < 0
        ):
            raise GovernanceConsistencyError(
                "revision must be integer >= 0."
            )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.resource_type,
            self.resource_id,
        )


@dataclass(frozen=True, slots=True)
class GovernanceConsistencySnapshot:
    """Canonical comparison snapshot."""

    policy_id: str
    policy_version: str
    policy_fingerprint: str

    evaluation_id: str
    evaluation_revision: int

    decision_fingerprint: str | None = None

    schema_version: int = (
        GOVERNANCE_CONSISTENCY_SCHEMA_VERSION
    )

    @property
    def fingerprint(self) -> str:
        payload = {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_fingerprint": (
                self.policy_fingerprint
            ),
            "evaluation_id": self.evaluation_id,
            "evaluation_revision": (
                self.evaluation_revision
            ),
            "decision_fingerprint": (
                self.decision_fingerprint
            ),
            "schema_version": self.schema_version,
        }

        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        return hashlib.sha256(raw).hexdigest()


class GovernanceConsistencyGuard:
    """Stateless deterministic consistency checks."""

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
            raise GovernanceVersionConflictError(
                "Governance policy fingerprint conflicts "
                "with expected material."
            )

    @staticmethod
    def assert_revision_current(
        *,
        expected_revision: int,
        actual_revision: int,
    ) -> None:
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or expected_revision < 0
        ):
            raise GovernanceConsistencyError(
                "expected_revision must be integer >= 0."
            )

        if (
            isinstance(actual_revision, bool)
            or not isinstance(actual_revision, int)
            or actual_revision < 0
        ):
            raise GovernanceConsistencyError(
                "actual_revision must be integer >= 0."
            )

        if expected_revision != actual_revision:
            raise GovernanceStaleEvaluationError(
                "Governance evaluation revision is stale."
            )

    @staticmethod
    def assert_identity_compatible(
        *,
        identity_key: tuple[str, str],
        fingerprint: str,
        existing_identity_key: tuple[str, str],
        existing_fingerprint: str,
    ) -> None:
        if identity_key != existing_identity_key:
            return

        if fingerprint != existing_fingerprint:
            raise GovernanceVersionConflictError(
                "Same governance identity contains "
                "conflicting material."
            )

    @staticmethod
    def assert_replay_safe(
        *,
        expected_fingerprint: str,
        replayed_fingerprint: str,
    ) -> None:
        if (
            expected_fingerprint
            != replayed_fingerprint
        ):
            raise GovernanceReplayConflictError(
                "Replayed governance material conflicts "
                "with authoritative fingerprint."
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
