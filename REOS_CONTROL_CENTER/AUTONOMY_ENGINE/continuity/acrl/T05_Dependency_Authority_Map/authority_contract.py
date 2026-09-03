"""ACRL T05 — machine-readable authority-map contract."""

from __future__ import annotations

from .dependency_authority_map import (
    DependencyAuthorityMap,
)


def validate_authority_contract(
    authority_map: DependencyAuthorityMap,
) -> None:
    """Validate the public T05 contract boundary."""

    if not isinstance(
        authority_map,
        DependencyAuthorityMap,
    ):
        raise TypeError(
            "authority_map must be DependencyAuthorityMap."
        )

    if authority_map.primary_authority != "REOS_STATE":
        raise ValueError(
            "T05 requires REOS_STATE as primary authority."
        )

    if not authority_map.sources:
        raise ValueError(
            "T05 requires at least one authority source."
        )

    if not authority_map.dependencies:
        raise ValueError(
            "T05 requires dependency relationships."
        )

    if (
        len(authority_map.fingerprint) != 64
        or any(
            char
            not in "0123456789abcdef"
            for char in authority_map.fingerprint
        )
    ):
        raise ValueError(
            "T05 fingerprint must be SHA-256."
        )


def contract_dict() -> dict[str, object]:
    """Return non-authorizing contract metadata."""

    return {
        "schema_version": "1.0",
        "layer": "T05",
        "name": "Dependency & Authority Map",
        "mode": "READ_ONLY",
        "authority": {
            "primary_execution_authority": "REOS_STATE"
        },
        "permissions": {
            "read_sources": True,
            "write_sources": False,
            "modify_authority": False,
            "modify_dependencies": False,
            "approve_changes": False,
            "authorize_execution": False,
            "repair_code": False
        },
        "guarantees": {
            "deterministic_identity": True,
            "conflict_detection": True,
            "duplicate_edge_detection": True,
            "self_dependency_detection": True
        }
    }


__all__ = [
    "contract_dict",
    "validate_authority_contract",
]