"""CORE-001 identity domain package."""

from .identity import (
    AccountStatus,
    Identity,
    IdentityAccount,
    IdentityStatus,
    IdentityType,
    PrivacyClass,
)

__all__ = [
    "AccountStatus",
    "Identity",
    "IdentityAccount",
    "IdentityStatus",
    "IdentityType",
    "PrivacyClass",
]
from .identity import ExternalIdentityReference, ExternalIdentityStatus
from .identity import IdentityRegistry, IdentityResolutionResult, IdentityResolutionStatus
from .tenant import (
    DataResidencyMode,
    IsolationProfile,
    OperatingMode,
    ProvisioningIntentStatus,
    Tenant,
    TenantKind,
    TenantProvisioningIntent,
    TenantStatus,
)
