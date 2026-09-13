"""
REOS Diagnostics
================

Read-only health and observability surface for HOMIO/REOS.

Authority:
    REOS_CONTROL_CENTER remains the canonical execution/state authority.

Diagnostics:
    - never mutate canonical state
    - never bypass Control Center
    - never replace ACRL
    - never replace Runtime
    - never become a second roadmap/state authority
"""

from .diagnostic_models import (
    DiagnosticCheck,
    DiagnosticEvidence,
    DiagnosticPosition,
    DiagnosticReport,
)
from .reos_health import REOSHealth

__all__ = [
    "DiagnosticCheck",
    "DiagnosticEvidence",
    "DiagnosticPosition",
    "DiagnosticReport",
    "REOSHealth",
]
