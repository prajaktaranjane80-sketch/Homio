"""ACRL T02 — Architecture Lock."""

from .architecture_contract import (
    contract_dict,
    validate_architecture_lock_contract,
)
from .architecture_drift import (
    ArchitectureDriftReport,
    ArchitectureDriftStatus,
    detect_architecture_drift,
)
from .architecture_identity import (
    ArchitectureIdentity,
    build_architecture_identity,
)
from .architecture_lock import (
    ARCHITECTURE_LOCK_SCHEMA_VERSION,
    ArchitectureDriftError,
    ArchitectureLock,
    ArchitectureLockError,
    ArchitectureLockIntegrityError,
    ArchitectureLockReader,
    ArchitectureLockSourceError,
    ArchitectureNotLockedError,
    read_architecture_lock,
)

__all__ = [
    "ARCHITECTURE_LOCK_SCHEMA_VERSION",
    "ArchitectureDriftError",
    "ArchitectureDriftReport",
    "ArchitectureDriftStatus",
    "ArchitectureIdentity",
    "ArchitectureLock",
    "ArchitectureLockError",
    "ArchitectureLockIntegrityError",
    "ArchitectureLockReader",
    "ArchitectureLockSourceError",
    "ArchitectureNotLockedError",
    "build_architecture_identity",
    "contract_dict",
    "detect_architecture_drift",
    "read_architecture_lock",
    "validate_architecture_lock_contract",
]