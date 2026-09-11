from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RepairDecision(str, Enum):
    REPAIR_PROPOSED = "REPAIR_PROPOSED"
    REPAIR_APPLIED = "REPAIR_APPLIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"


class RepairReason(str, Enum):
    VALID = "VALID"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    AUTHORIZATION_INVALID = "AUTHORIZATION_INVALID"
    SCOPE_ESCAPE = "SCOPE_ESCAPE"
    BASELINE_DRIFT = "BASELINE_DRIFT"
    INVALID_PATCH = "INVALID_PATCH"
    PATCH_TOO_LARGE = "PATCH_TOO_LARGE"
    PROTECTED_PATH = "PROTECTED_PATH"
    SYNTAX_FAILURE = "SYNTAX_FAILURE"
    TEST_FAILURE = "TEST_FAILURE"
    REGRESSION_FAILURE = "REGRESSION_FAILURE"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class RepairPolicy:
    schema_version: str = "1.0"
    policy_version: str = "1.0"

    max_files: int = 20
    max_patch_bytes: int = 512 * 1024
    max_attempts: int = 3

    allow_state_mutation: bool = False
    allow_architecture_mutation: bool = False
    allow_authorization_mutation: bool = False
    allow_main_repository_mutation: bool = False


@dataclass(frozen=True, slots=True)
class RepairRequest:
    repair_id: str
    authorization_fingerprint: str
    authorization_nonce: str
    diagnosis_fingerprint: str
    impact_fingerprint: str
    baseline_fingerprint: str
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    candidate_patch: str
    attempt: int = 1
    policy_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "repair_id": self.repair_id,
            "authorization_fingerprint": self.authorization_fingerprint,
            "authorization_nonce": self.authorization_nonce,
            "diagnosis_fingerprint": self.diagnosis_fingerprint,
            "impact_fingerprint": self.impact_fingerprint,
            "baseline_fingerprint": self.baseline_fingerprint,
            "allowed_paths": list(self.allowed_paths),
            "forbidden_paths": list(self.forbidden_paths),
            "candidate_patch": self.candidate_patch,
            "attempt": self.attempt,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class BaselineSnapshot:
    repository_root: str
    tree_fingerprint: str
    file_fingerprints: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository_root": self.repository_root,
            "tree_fingerprint": self.tree_fingerprint,
            "file_fingerprints": [
                {
                    "path": path,
                    "fingerprint": digest,
                }
                for path, digest in self.file_fingerprints
            ],
        }


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    syntax_passed: bool
    tests_passed: bool | None
    regression_passed: bool | None
    external_executor: str
    evidence_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "syntax_passed": self.syntax_passed,
            "tests_passed": self.tests_passed,
            "regression_passed": self.regression_passed,
            "external_executor": self.external_executor,
            "evidence_fingerprint": self.evidence_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class PatchVerification:
    passed: bool
    changed_paths: tuple[str, ...]
    patch_fingerprint: str
    final_tree_fingerprint: str
    evidence: VerificationEvidence
    reason: RepairReason

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "changed_paths": list(self.changed_paths),
            "patch_fingerprint": self.patch_fingerprint,
            "final_tree_fingerprint": self.final_tree_fingerprint,
            "evidence": self.evidence.to_dict(),
            "reason": self.reason.value,
        }


@dataclass(frozen=True, slots=True)
class RepairResult:
    schema_version: str
    decision: RepairDecision
    reason: RepairReason
    repair_id: str
    authorization_fingerprint: str
    diagnosis_fingerprint: str
    baseline_fingerprint: str
    patch_fingerprint: str
    final_tree_fingerprint: str
    changed_paths: tuple[str, ...]
    attempt: int
    verification: PatchVerification | None
    evidence_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "repair_id": self.repair_id,
            "authorization_fingerprint": self.authorization_fingerprint,
            "diagnosis_fingerprint": self.diagnosis_fingerprint,
            "baseline_fingerprint": self.baseline_fingerprint,
            "patch_fingerprint": self.patch_fingerprint,
            "final_tree_fingerprint": self.final_tree_fingerprint,
            "changed_paths": list(self.changed_paths),
            "attempt": self.attempt,
            "verification": (
                self.verification.to_dict()
                if self.verification
                else None
            ),
            "evidence_fingerprint": self.evidence_fingerprint,
        }
