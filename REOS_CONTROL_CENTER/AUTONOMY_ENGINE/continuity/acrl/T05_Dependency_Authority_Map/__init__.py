"""ACRL T05 — Dependency & Authority Map."""

from .authority_contract import (
    contract_dict,
    validate_authority_contract,
)
from .authority_identity import (
    AuthorityMapIdentity,
    build_authority_map_identity,
)
from .authority_normalization import (
    canonical_map_payload,
    normalize_dependencies,
    normalize_sources,
)
from .authority_validation import (
    AuthorityValidationReport,
    AuthorityValidationStatus,
    validate_authority_map,
)
from .dependency_authority_map import (
    AuthorityConflictError,
    AuthorityDependency,
    AuthorityLevel,
    AuthorityMapError,
    AuthorityMapIntegrityError,
    AuthoritySource,
    DependencyAuthorityMap,
    DependencyAuthorityMapBuilder,
    DependencyType,
    build_dependency_authority_map,
)

__all__ = [
    "AuthorityConflictError",
    "AuthorityDependency",
    "AuthorityLevel",
    "AuthorityMapError",
    "AuthorityMapIdentity",
    "AuthorityMapIntegrityError",
    "AuthoritySource",
    "AuthorityValidationReport",
    "AuthorityValidationStatus",
    "DependencyAuthorityMap",
    "DependencyAuthorityMapBuilder",
    "DependencyType",
    "build_authority_map_identity",
    "build_dependency_authority_map",
    "canonical_map_payload",
    "contract_dict",
    "normalize_dependencies",
    "normalize_sources",
    "validate_authority_contract",
    "validate_authority_map",
]