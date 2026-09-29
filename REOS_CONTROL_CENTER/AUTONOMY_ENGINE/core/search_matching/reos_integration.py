"""
CORE-005 / Point 10 — REOS Integration Contract.

Defines the hard boundary between CORE-005 Search & Matching
and the REOS Control Center.

CORE-005 may:
- identify its architecture/component
- report compatibility metadata
- produce verification evidence
- expose read-only integration contracts

CORE-005 may NOT:
- mutate state.json
- choose the next Control Center task
- approve/freeze itself
- alter Control Center gates
- bypass execution authorization
- become project-state authority

The Control Center remains the canonical project-state authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class REOSIntegrationError(ValueError):
    """Base REOS integration error."""


class REOSAuthorityViolation(
    REOSIntegrationError
):
    """Raised when CORE-005 attempts to own project state."""


class REOSCompatibilityError(
    REOSIntegrationError
):
    """Raised when integration requirements are incompatible."""


class REOSVerificationError(
    REOSIntegrationError
):
    """Raised when verification evidence is malformed."""


class REOSIntegrationDecision(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"


REOS_AUTHORITY = "REOS_CONTROL_CENTER"
CORE_005_COMPONENT = "CORE-005"
REOS_INTEGRATION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class REOSCompatibilityProfile:
    """
    Read-only compatibility declaration.

    This is not a copy of Control Center state.
    """

    component: str = CORE_005_COMPONENT
    authority: str = REOS_AUTHORITY
    schema_version: int = REOS_INTEGRATION_SCHEMA_VERSION

    canonical_state_owner: str = "REOS_CONTROL_CENTER"
    project_state_mutation_allowed: bool = False
    roadmap_mutation_allowed: bool = False
    gate_approval_allowed: bool = False
    execution_authorization_owned: bool = False

    def __post_init__(self) -> None:
        if self.component != CORE_005_COMPONENT:
            raise REOSCompatibilityError(
                "Unexpected component identity."
            )

        if self.authority != REOS_AUTHORITY:
            raise REOSCompatibilityError(
                "Unexpected REOS authority."
            )

        if (
            isinstance(
                self.schema_version,
                bool,
            )
            or not isinstance(
                self.schema_version,
                int,
            )
            or self.schema_version < 1
        ):
            raise REOSCompatibilityError(
                "schema_version must be positive."
            )

        if self.project_state_mutation_allowed:
            raise REOSAuthorityViolation(
                "CORE-005 cannot mutate project state."
            )

        if self.roadmap_mutation_allowed:
            raise REOSAuthorityViolation(
                "CORE-005 cannot mutate roadmap."
            )

        if self.gate_approval_allowed:
            raise REOSAuthorityViolation(
                "CORE-005 cannot approve its own gate."
            )

        if self.execution_authorization_owned:
            raise REOSAuthorityViolation(
                "CORE-005 cannot own execution authorization."
            )


@dataclass(frozen=True, slots=True)
class REOSVerificationEvidence:
    """
    Verification evidence produced by CORE-005.

    Evidence is informational.
    Approval remains external.
    """

    component: str
    verification_id: str
    verified: bool
    test_reference: str | None = None
    repository_reference: str | None = None
    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.component,
                str,
            )
            or not self.component.strip()
        ):
            raise REOSVerificationError(
                "component must be non-empty."
            )

        if (
            not isinstance(
                self.verification_id,
                str,
            )
            or not self.verification_id.strip()
        ):
            raise REOSVerificationError(
                "verification_id must be non-empty."
            )

        if not isinstance(
            self.verified,
            bool,
        ):
            raise REOSVerificationError(
                "verified must be bool."
            )

        if self.test_reference is not None:
            if (
                not isinstance(
                    self.test_reference,
                    str,
                )
                or not self.test_reference.strip()
            ):
                raise REOSVerificationError(
                    "test_reference must be non-empty when supplied."
                )

        if self.repository_reference is not None:
            if (
                not isinstance(
                    self.repository_reference,
                    str,
                )
                or not self.repository_reference.strip()
            ):
                raise REOSVerificationError(
                    "repository_reference must be non-empty."
                )

        if not isinstance(
            self.evidence,
            Mapping,
        ):
            raise REOSVerificationError(
                "evidence must be a mapping."
            )

        object.__setattr__(
            self,
            "evidence",
            dict(self.evidence),
        )


@dataclass(frozen=True, slots=True)
class REOSIntegrationReport:
    """
    Read-only CORE-005 integration report.

    The report cannot mutate the project state.
    """

    profile: REOSCompatibilityProfile
    decision: REOSIntegrationDecision
    verification: REOSVerificationEvidence | None = None
    compatibility_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.profile,
            REOSCompatibilityProfile,
        ):
            raise REOSIntegrationError(
                "profile must be REOSCompatibilityProfile."
            )

        if (
            not isinstance(
                self.decision,
                REOSIntegrationDecision,
            )
        ):
            raise REOSIntegrationError(
                "decision must be REOSIntegrationDecision."
            )

        if self.verification is not None:
            if not isinstance(
                self.verification,
                REOSVerificationEvidence,
            ):
                raise REOSVerificationError(
                    "Invalid verification evidence."
                )

        if isinstance(
            self.compatibility_notes,
            (str, bytes),
        ):
            raise REOSIntegrationError(
                "compatibility_notes must be iterable."
            )

        object.__setattr__(
            self,
            "compatibility_notes",
            tuple(
                str(note)
                for note in self.compatibility_notes
            ),
        )


@dataclass(frozen=True, slots=True)
class REOSIntegrationContract:
    """
    CORE-005 <-> REOS Control Center contract.

    This class is intentionally incapable of writing state.json.
    """

    profile: REOSCompatibilityProfile = (
        REOSCompatibilityProfile()
    )

    def validate_authority_boundary(
        self,
    ) -> None:
        if (
            self.profile.authority
            != REOS_AUTHORITY
        ):
            raise REOSAuthorityViolation(
                "REOS authority mismatch."
            )

        if (
            self.profile.canonical_state_owner
            != REOS_AUTHORITY
        ):
            raise REOSAuthorityViolation(
                "Canonical state owner must remain "
                "REOS_CONTROL_CENTER."
            )

        if self.profile.project_state_mutation_allowed:
            raise REOSAuthorityViolation(
                "Project-state mutation is forbidden."
            )

        if self.profile.roadmap_mutation_allowed:
            raise REOSAuthorityViolation(
                "Roadmap mutation is forbidden."
            )

        if self.profile.gate_approval_allowed:
            raise REOSAuthorityViolation(
                "Gate approval is forbidden."
            )

        if self.profile.execution_authorization_owned:
            raise REOSAuthorityViolation(
                "Execution authorization ownership is forbidden."
            )

    def verification_required(
        self,
        verification: REOSVerificationEvidence | None,
    ) -> bool:
        if verification is None:
            return True

        return not verification.verified

    def verify_compatibility(
        self,
        verification: REOSVerificationEvidence | None = None,
    ) -> REOSIntegrationReport:
        self.validate_authority_boundary()

        if verification is None:
            return REOSIntegrationReport(
                profile=self.profile,
                decision=(
                    REOSIntegrationDecision
                    .VERIFICATION_REQUIRED
                ),
                verification=None,
                compatibility_notes=(
                    "CORE-005 exposes evidence only.",
                    "Control Center retains canonical state.",
                    "CORE-005 cannot self-approve.",
                    "Execution authorization remains external.",
                ),
            )

        if verification.component != CORE_005_COMPONENT:
            raise REOSVerificationError(
                "Verification evidence belongs to another component."
            )

        if not verification.verified:
            return REOSIntegrationReport(
                profile=self.profile,
                decision=(
                    REOSIntegrationDecision
                    .VERIFICATION_REQUIRED
                ),
                verification=verification,
                compatibility_notes=(
                    "Verification evidence is not yet green.",
                ),
            )

        return REOSIntegrationReport(
            profile=self.profile,
            decision=(
                REOSIntegrationDecision.COMPATIBLE
            ),
            verification=verification,
            compatibility_notes=(
                "CORE-005 remains subordinate to REOS Control Center.",
                "No project-state mutation is exposed.",
                "No roadmap mutation is exposed.",
                "No autonomous gate approval is exposed.",
                "Execution authorization remains external.",
            ),
        )

    def reproducibility_fingerprint(
        self,
        report: REOSIntegrationReport,
    ) -> str:
        if not isinstance(
            report,
            REOSIntegrationReport,
        ):
            raise REOSIntegrationError(
                "report must be REOSIntegrationReport."
            )

        canonical = {
            "profile": {
                "component": report.profile.component,
                "authority": report.profile.authority,
                "schema_version": (
                    report.profile.schema_version
                ),
                "canonical_state_owner": (
                    report.profile.canonical_state_owner
                ),
                "project_state_mutation_allowed": (
                    report.profile.project_state_mutation_allowed
                ),
                "roadmap_mutation_allowed": (
                    report.profile.roadmap_mutation_allowed
                ),
                "gate_approval_allowed": (
                    report.profile.gate_approval_allowed
                ),
                "execution_authorization_owned": (
                    report.profile.execution_authorization_owned
                ),
            },
            "decision": report.decision.value,
            "verification": (
                {
                    "verification_id": (
                        report.verification.verification_id
                    ),
                    "verified": (
                        report.verification.verified
                    ),
                    "test_reference": (
                        report.verification.test_reference
                    ),
                    "repository_reference": (
                        report.verification.repository_reference
                    ),
                    "evidence": dict(
                        report.verification.evidence
                    ),
                }
                if report.verification is not None
                else None
            ),
            "compatibility_notes": list(
                report.compatibility_notes
            ),
        }

        encoded = json.dumps(
            canonical,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            encoded.encode("utf-8")
        ).hexdigest()


__all__ = [
    "REOS_AUTHORITY",
    "CORE_005_COMPONENT",
    "REOS_INTEGRATION_SCHEMA_VERSION",
    "REOSIntegrationError",
    "REOSAuthorityViolation",
    "REOSCompatibilityError",
    "REOSVerificationError",
    "REOSIntegrationDecision",
    "REOSCompatibilityProfile",
    "REOSVerificationEvidence",
    "REOSIntegrationReport",
    "REOSIntegrationContract",
]
