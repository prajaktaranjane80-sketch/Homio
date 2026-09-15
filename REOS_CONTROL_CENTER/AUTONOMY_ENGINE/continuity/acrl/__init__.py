"""ACRL — Autonomous Continuity & Recovery Layer."""

from .project_dna import (
    ProjectDNA,
    ProjectDNAError,
    ProjectDNAIntegrityError,
    ProjectDNASourceError,
    ProjectDNAReader,
    read_project_dna,
)

from .repository_context import (
    AUTHORITY,
    SCHEMA_VERSION,
    RepositoryContextDecision,
    RepositoryContextReason,
    RepositoryContextError,
    RepositoryContextAuthorityError,
    RepositoryContextValidationError,
    RepositoryContextRequest,
    RepositoryContextReport,
    RepositoryContextEngine,
    resolve_repository_context,
)

__all__ = [
    "ProjectDNA",
    "ProjectDNAError",
    "ProjectDNAIntegrityError",
    "ProjectDNASourceError",
    "ProjectDNAReader",
    "read_project_dna",
    "AUTHORITY",
    "SCHEMA_VERSION",
    "RepositoryContextDecision",
    "RepositoryContextReason",
    "RepositoryContextError",
    "RepositoryContextAuthorityError",
    "RepositoryContextValidationError",
    "RepositoryContextRequest",
    "RepositoryContextReport",
    "RepositoryContextEngine",
    "resolve_repository_context",
]
