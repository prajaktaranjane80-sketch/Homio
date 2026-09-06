"""ACRL T13 controller integration compatibility bridge.

Canonical implementation:
    T13_Controller_Integration.controller_integration

This module preserves the historical root import path without
duplicating implementation.
"""

from .T13_Controller_Integration.controller_integration import (
    ACRLContinuityView,
    AUTHORITY,
    HASH_ALGORITHM,
    SCHEMA_VERSION,
    ControllerIntegrationAuthorityError,
    ControllerIntegrationConflictError,
    ControllerIntegrationEngine,
    ControllerIntegrationError,
    ControllerIntegrationReport,
    ControllerIntegrationRequest,
    ControllerIntegrationValidationError,
    ControllerStateView,
    IntegrationDecision,
    IntegrationReason,
    controller_resume_authorized,
    integrate_controller,
)

__all__ = [
    "ACRLContinuityView",
    "AUTHORITY",
    "HASH_ALGORITHM",
    "SCHEMA_VERSION",
    "ControllerIntegrationAuthorityError",
    "ControllerIntegrationConflictError",
    "ControllerIntegrationEngine",
    "ControllerIntegrationError",
    "ControllerIntegrationReport",
    "ControllerIntegrationRequest",
    "ControllerIntegrationValidationError",
    "ControllerStateView",
    "IntegrationDecision",
    "IntegrationReason",
    "controller_resume_authorized",
    "integrate_controller",
]
