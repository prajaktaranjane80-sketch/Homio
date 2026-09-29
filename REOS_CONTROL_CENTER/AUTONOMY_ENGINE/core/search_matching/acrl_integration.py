"""
CORE-005 / Point 11 — ACRL Integration Contract.

ACRL remains the repository-continuity / reconstruction authority.
CORE-005 only exposes enough deterministic metadata for ACRL to:

- reconstruct the search projection contract
- discover dependencies
- discover schema/index versions
- discover ranking version
- discover evidence metadata
- reproduce deterministic rebuild inputs
- detect projection/schema/ranking drift

This module does NOT:
- implement ACRL
- create a second continuity engine
- mutate ACRL state
- mutate REOS Control Center state
- become source of truth
- execute a rebuild itself
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping

from .search_index_contract import (
    EXPECTED_INDEX_FINGERPRINT,
    SEARCH_INDEXED_FIELDS,
    SEARCH_INDEX_VERSION,
    SEARCH_SCHEMA_VERSION,
    SEARCH_SOURCE_DOMAIN,
)
from .search_ranking import RANKING_VERSION


class ACRLIntegrationError(ValueError):
    """Base CORE-005 ACRL integration error."""


class ACRLDiscoverabilityError(
    ACRLIntegrationError
):
    """Raised when reconstruction metadata is incomplete."""


class ACRLDriftError(
    ACRLIntegrationError
):
    """Raised when supplied runtime metadata drifts."""


ACRL_CONTRACT_VERSION = 1
CORE_005_COMPONENT = "CORE-005"


@dataclass(frozen=True, slots=True)
class ACRLDependency:
    """
    One explicitly discoverable CORE-005 dependency.
    """

    component: str
    role: str
    required: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.component, str)
            or not self.component.strip()
        ):
            raise ACRLDiscoverabilityError(
                "dependency component must be non-empty."
            )

        if (
            not isinstance(self.role, str)
            or not self.role.strip()
        ):
            raise ACRLDiscoverabilityError(
                "dependency role must be non-empty."
            )

        if not isinstance(
            self.required,
            bool,
        ):
            raise ACRLDiscoverabilityError(
                "dependency required must be bool."
            )


@dataclass(frozen=True, slots=True)
class ACRLReconstructionManifest:
    """
    Machine-readable reconstruction metadata.

    It describes how CORE-005 can be reconstructed;
    it does not perform reconstruction.
    """

    component: str = CORE_005_COMPONENT
    contract_version: int = ACRL_CONTRACT_VERSION

    source_domain: str = SEARCH_SOURCE_DOMAIN
    schema_version: int = SEARCH_SCHEMA_VERSION
    index_version: int = SEARCH_INDEX_VERSION
    index_fingerprint: str = (
        EXPECTED_INDEX_FINGERPRINT
    )

    indexed_fields: tuple[
        str, ...
    ] = SEARCH_INDEXED_FIELDS

    ranking_version: int = RANKING_VERSION

    dependencies: tuple[
        ACRLDependency, ...
    ] = field(
        default_factory=lambda: (
            ACRLDependency(
                component="CORE-004.Inventory",
                role="canonical_source_of_truth",
            ),
            ACRLDependency(
                component="CORE-002.EventPlatform",
                role="source_event_contract",
            ),
            ACRLDependency(
                component="REOS_CONTROL_CENTER",
                role="project_state_authority",
            ),
            ACRLDependency(
                component="ACRL",
                role="continuity_reconstruction_authority",
            ),
        )
    )

    reconstruction_steps: tuple[
        str, ...
    ] = (
        "discover_source_contract",
        "discover_index_schema",
        "discover_projection_version",
        "rebuild_derived_projection_from_source",
        "discover_ranking_version",
        "discover_observability_evidence",
        "compare_fingerprints",
        "report_drift",
    )

    def __post_init__(self) -> None:
        if self.component != CORE_005_COMPONENT:
            raise ACRLDiscoverabilityError(
                "Unexpected CORE-005 component identity."
            )

        if (
            isinstance(
                self.contract_version,
                bool,
            )
            or not isinstance(
                self.contract_version,
                int,
            )
            or self.contract_version < 1
        ):
            raise ACRLDiscoverabilityError(
                "contract_version must be positive."
            )

        for name, value in (
            ("schema_version", self.schema_version),
            ("index_version", self.index_version),
            ("ranking_version", self.ranking_version),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
            ):
                raise ACRLDiscoverabilityError(
                    f"{name} must be positive."
                )

        if (
            not isinstance(
                self.index_fingerprint,
                str,
            )
            or not self.index_fingerprint.strip()
        ):
            raise ACRLDiscoverabilityError(
                "index_fingerprint must be non-empty."
            )

        if not self.indexed_fields:
            raise ACRLDiscoverabilityError(
                "indexed_fields cannot be empty."
            )

        if len(
            set(self.indexed_fields)
        ) != len(
            self.indexed_fields
        ):
            raise ACRLDiscoverabilityError(
                "indexed_fields cannot contain duplicates."
            )

        if not self.dependencies:
            raise ACRLDiscoverabilityError(
                "dependencies cannot be empty."
            )

        if not self.reconstruction_steps:
            raise ACRLDiscoverabilityError(
                "reconstruction_steps cannot be empty."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "contract_version": self.contract_version,
            "source_domain": self.source_domain,
            "schema_version": self.schema_version,
            "index_version": self.index_version,
            "index_fingerprint": self.index_fingerprint,
            "indexed_fields": list(
                self.indexed_fields
            ),
            "ranking_version": self.ranking_version,
            "dependencies": [
                {
                    "component": dependency.component,
                    "role": dependency.role,
                    "required": dependency.required,
                }
                for dependency in self.dependencies
            ],
            "reconstruction_steps": list(
                self.reconstruction_steps
            ),
        }

    def fingerprint(self) -> str:
        encoded = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            encoded.encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class ACRLDriftReport:
    """
    Deterministic drift report.
    """

    drift_detected: bool
    differences: tuple[str, ...]
    expected_fingerprint: str
    observed_fingerprint: str | None

    @property
    def clean(self) -> bool:
        return not self.drift_detected


@dataclass(frozen=True, slots=True)
class ACRLIntegrationContract:
    """
    Read-only contract exposed to ACRL.
    """

    manifest: ACRLReconstructionManifest = (
        ACRLReconstructionManifest()
    )

    def discover(
        self,
    ) -> ACRLReconstructionManifest:
        return self.manifest

    def verify_runtime(
        self,
        *,
        schema_version: int,
        index_version: int,
        index_fingerprint: str,
        ranking_version: int,
    ) -> ACRLDriftReport:
        differences: list[str] = []

        if (
            schema_version
            != self.manifest.schema_version
        ):
            differences.append(
                "schema_version"
            )

        if (
            index_version
            != self.manifest.index_version
        ):
            differences.append(
                "index_version"
            )

        if (
            index_fingerprint
            != self.manifest.index_fingerprint
        ):
            differences.append(
                "index_fingerprint"
            )

        if (
            ranking_version
            != self.manifest.ranking_version
        ):
            differences.append(
                "ranking_version"
            )

        observed_payload = {
            "schema_version": schema_version,
            "index_version": index_version,
            "index_fingerprint": index_fingerprint,
            "ranking_version": ranking_version,
        }

        observed_encoded = json.dumps(
            observed_payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        expected_payload = {
            "schema_version": (
                self.manifest.schema_version
            ),
            "index_version": (
                self.manifest.index_version
            ),
            "index_fingerprint": (
                self.manifest.index_fingerprint
            ),
            "ranking_version": (
                self.manifest.ranking_version
            ),
        }

        expected_encoded = json.dumps(
            expected_payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        expected_fingerprint = hashlib.sha256(
            expected_encoded.encode("utf-8")
        ).hexdigest()

        observed_fingerprint = hashlib.sha256(
            observed_encoded.encode("utf-8")
        ).hexdigest()

        return ACRLDriftReport(
            drift_detected=bool(differences),
            differences=tuple(
                differences
            ),
            expected_fingerprint=(
                expected_fingerprint
            ),
            observed_fingerprint=(
                observed_fingerprint
            ),
        )


__all__ = [
    "ACRL_CONTRACT_VERSION",
    "CORE_005_COMPONENT",
    "ACRLIntegrationError",
    "ACRLDiscoverabilityError",
    "ACRLDriftError",
    "ACRLDependency",
    "ACRLReconstructionManifest",
    "ACRLDriftReport",
    "ACRLIntegrationContract",
]
