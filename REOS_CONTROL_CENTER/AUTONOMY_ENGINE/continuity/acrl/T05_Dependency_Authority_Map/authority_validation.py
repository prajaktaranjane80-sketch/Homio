"""ACRL T05 — authority/dependency validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .dependency_authority_map import (
    AuthorityLevel,
    DependencyAuthorityMap,
    DependencyType,
)


class AuthorityValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


@dataclass(frozen=True)
class AuthorityValidationReport:
    """Immutable T05 validation result."""

    status: AuthorityValidationStatus
    checks: tuple[str, ...]
    failures: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return (
            self.status
            == AuthorityValidationStatus.VALID
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "valid": self.valid,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def validate_authority_map(
    authority_map: DependencyAuthorityMap,
) -> AuthorityValidationReport:
    """Validate T05 graph integrity without changing it."""

    if not isinstance(
        authority_map,
        DependencyAuthorityMap,
    ):
        raise TypeError(
            "authority_map must be DependencyAuthorityMap."
        )

    checks: list[str] = []
    failures: list[str] = []

    def check(
        name: str,
        condition: bool,
        reason: str,
    ) -> None:
        checks.append(name)

        if not condition:
            failures.append(reason)

    source_ids = [
        source.source_id
        for source in authority_map.sources
    ]

    check(
        "source_ids_unique",
        len(source_ids) == len(set(source_ids)),
        "Authority source IDs are duplicated.",
    )

    dependency_keys = [
        (
            item.consumer,
            item.source,
            item.dependency_type.value,
        )
        for item in authority_map.dependencies
    ]

    check(
        "dependency_edges_unique",
        len(dependency_keys)
        == len(set(dependency_keys)),
        "Duplicate dependency edge detected.",
    )

    self_dependencies = [
        item
        for item in authority_map.dependencies
        if item.consumer == item.source
    ]

    check(
        "no_self_dependency",
        not self_dependencies,
        "Self dependency is not allowed.",
    )

    authoritative_sources = {
        source.source_id
        for source in authority_map.sources
        if source.level
        == AuthorityLevel.AUTHORITATIVE
    }

    check(
        "primary_is_authoritative",
        authority_map.primary_authority
        in authoritative_sources,
        "Primary authority is not authoritative.",
    )

    acrl_authoritative = {
        item.source
        for item in authority_map.dependencies
        if (
            item.consumer == "ACRL"
            and item.dependency_type
            == DependencyType.AUTHORITATIVE
        )
    }

    check(
        "acrl_has_primary_state_dependency",
        "REOS_STATE" in acrl_authoritative,
        "ACRL does not depend authoritatively on REOS_STATE.",
    )

    context_sources = {
        source.source_id
        for source in authority_map.sources
        if source.level == AuthorityLevel.CONTEXT
    }

    for dependency in authority_map.dependencies:
        if (
            dependency.source in context_sources
            and dependency.dependency_type
            != DependencyType.CONTEXT_ONLY
        ):
            failures.append(
                "Context source has non-context dependency: "
                f"{dependency.source}"
            )

    checks.append(
        "context_dependency_classification"
    )

    derived_sources = {
        source.source_id
        for source in authority_map.sources
        if source.level == AuthorityLevel.DERIVED
    }

    for dependency in authority_map.dependencies:
        if (
            dependency.source in derived_sources
            and dependency.dependency_type
            == DependencyType.AUTHORITATIVE
        ):
            failures.append(
                "Derived source is incorrectly treated as authoritative: "
                f"{dependency.source}"
            )

    checks.append(
        "derived_dependency_classification"
    )

    return AuthorityValidationReport(
        status=(
            AuthorityValidationStatus.VALID
            if not failures
            else AuthorityValidationStatus.INVALID
        ),
        checks=tuple(checks),
        failures=tuple(failures),
    )


__all__ = [
    "AuthorityValidationReport",
    "AuthorityValidationStatus",
    "validate_authority_map",
]