"""ACRL compatibility bridge for the relocated T01 Project DNA module.

This file contains no Project DNA implementation.
It preserves the historical ACRL import path while the real implementation
lives under T01_Project_DNA.
"""

from .T01_Project_DNA.project_dna import (
    DNA_SCHEMA_VERSION,
    ProjectDNA,
    ProjectDNAError,
    ProjectDNAIntegrityError,
    ProjectDNASourceError,
    ProjectDNAReader,
    read_project_dna,
)

__all__ = [
    "DNA_SCHEMA_VERSION",
    "ProjectDNA",
    "ProjectDNAError",
    "ProjectDNAIntegrityError",
    "ProjectDNASourceError",
    "ProjectDNAReader",
    "read_project_dna",
]