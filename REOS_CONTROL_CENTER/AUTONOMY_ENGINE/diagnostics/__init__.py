"""
REOS Diagnostics
================

Read-only diagnostic surface for the HOMIO/REOS autonomous system.

This package does NOT:
- own canonical state
- modify state.json
- execute mutations
- replace REOS_CONTROL_CENTER
- replace ACRL
- replace AUTONOMY_ENGINE runtime
- create a parallel roadmap

It only verifies the health/integrity of existing authoritative layers.
"""

from .reos_health import (
    HealthCheck,
    HealthReport,
    REOSHealth,
    run_health_check,
)

__all__ = [
    "HealthCheck",
    "HealthReport",
    "REOSHealth",
    "run_health_check",
]
