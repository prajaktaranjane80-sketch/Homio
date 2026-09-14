"""REOS Control Plane.

Canonical control-plane package for REOS.

The control plane does not replace:

* REOS_CONTROL_CENTER/data/state.json as canonical state
* AUTONOMY_ENGINE as intelligence/execution orchestration
* ACRL as continuity/reconstruction capability
* AUTONOMY_ENGINE/integration as compatibility contract

It coordinates and verifies those existing capabilities under the
authority of REOS_CONTROL_CENTER.
"""

from .control_plane import (
ControlPlane,
ControlPlaneBlockReason,
ControlPlaneDecision,
ControlPlaneSnapshot,
)

**all** = [
"ControlPlane",
"ControlPlaneBlockReason",
"ControlPlaneDecision",
"ControlPlaneSnapshot",
]
