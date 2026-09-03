"""ACRL T05 — deterministic authority-map identity."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .authority_normalization import canonical_map_payload
from .dependency_authority_map import (
    DependencyAuthorityMap,
)


@dataclass(frozen=True)
class AuthorityMapIdentity:
    """Immutable identity of one authority/dependency graph."""

    schema_version: str
    primary_authority: str
    canonical_sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "primary_authority": self.primary_authority,
            "canonical_sha256": self.canonical_sha256,
        }

    def identity_key(self) -> str:
        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


def build_authority_map_identity(
    authority_map: DependencyAuthorityMap,
) -> AuthorityMapIdentity:
    """Build stable identity independent of collection ordering."""

    if not isinstance(
        authority_map,
        DependencyAuthorityMap,
    ):
        raise TypeError(
            "authority_map must be DependencyAuthorityMap."
        )

    payload = canonical_map_payload(
        authority_map.sources,
        authority_map.dependencies,
    )

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return AuthorityMapIdentity(
        schema_version="1.0",
        primary_authority=(
            authority_map.primary_authority
        ),
        canonical_sha256=digest,
    )


__all__ = [
    "AuthorityMapIdentity",
    "build_authority_map_identity",
]