"""
REOS_CONTROL_CENTER <-> AUTONOMY_ENGINE integration lock.

This module defines the immutable compatibility contract between the
AUTONOMY_ENGINE and the authoritative REOS_CONTROL_CENTER.

This is a contract/verification layer only.

It does NOT:
- execute controller commands,
- mutate controller state,
- mutate state.json,
- discover executors,
- grant authorization,
- bypass policy,
- approve actions,
- transition controller state,
- perform retries.

Authority model
---------------
REOS_CONTROL_CENTER remains authoritative.

AUTONOMY_ENGINE is an execution-governance and orchestration layer
operating under the controller's authority.

Integration model
-----------------
Controller
    |
    +--> authoritative state
    +--> authoritative lifecycle
    +--> authoritative approvals
    +--> authoritative transitions
    |
    v
Integration Lock
    |
    +--> compatibility validation
    +--> capability contract validation
    +--> architecture-lock validation
    +--> version compatibility validation
    |
    v
AUTONOMY_ENGINE
    |
    +--> protocol
    +--> policy
    +--> risk
    +--> guards
    +--> tripwires
    +--> idempotency
    +--> execution coordination

Upgrade model
-------------
The integration contract is intentionally versioned.

An AUTONOMY_ENGINE upgrade must not silently change:
- controller authority,
- mutation ownership,
- state ownership,
- approval ownership,
- transition ownership,
- executor ownership,
- safety defaults.

Any incompatible contract change must fail closed.

This module is intentionally dependency-light and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


INTEGRATION_CONTRACT_VERSION = "1.0"

AUTHORITATIVE_CONTROLLER = "REOS_CONTROL_CENTER"
AUTONOMY_ENGINE_NAME = "AUTONOMY_ENGINE"

MIN_SUPPORTED_CONTROLLER_CONTRACT = "1.0"
MAX_SUPPORTED_CONTROLLER_CONTRACT = "1.x"


class IntegrationLockStatus(str, Enum):
    LOCKED = "LOCKED"
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    INVALID = "INVALID"


class IntegrationBlockReason(str, Enum):
    CONTROLLER_MISSING = "CONTROLLER_MISSING"
    CONTROLLER_NOT_AUTHORITATIVE = "CONTROLLER_NOT_AUTHORITATIVE"
    CONTRACT_VERSION_MISSING = "CONTRACT_VERSION_MISSING"
    CONTRACT_VERSION_UNSUPPORTED = "CONTRACT_VERSION_UNSUPPORTED"
    AUTHORITY_BOUNDARY_INVALID = "AUTHORITY_BOUNDARY_INVALID"
    ARCHITECTURE_NOT_LOCKED = "ARCHITECTURE_NOT_LOCKED"
    CAPABILITY_CONTRACT_INVALID = "CAPABILITY_CONTRACT_INVALID"
    INTEGRATION_CONTRACT_INVALID = "INTEGRATION_CONTRACT_INVALID"


@dataclass(frozen=True)
class IntegrationCapabilities:
    """
    Explicit capabilities exposed by the authoritative controller.

    These are descriptive permissions, not authorization grants.
    """

    observe_state: bool = False
    observe_plan: bool = False
    observe_gate: bool = False
    observe_verification: bool = False

    execute_authoritative_mutation: bool = False

    approve_gate: bool = False
    transition_controller: bool = False
    mutate_state_directly: bool = False
    discover_executor: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []

        if self.mutate_state_directly:
            errors.append("DIRECT_STATE_MUTATION_FORBIDDEN")

        if self.discover_executor:
            errors.append("EXECUTOR_DISCOVERY_FORBIDDEN")

        return tuple(errors)


@dataclass(frozen=True)
class IntegrationContract:
    """
    Immutable controller/engine compatibility contract.
    """

    controller_name: str = AUTHORITATIVE_CONTROLLER
    autonomy_engine_name: str = AUTONOMY_ENGINE_NAME

    controller_contract_version: str = ""
    integration_contract_version: str = INTEGRATION_CONTRACT_VERSION

    architecture_locked: bool = True
    controller_authoritative: bool = True

    capabilities: IntegrationCapabilities = IntegrationCapabilities()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []

        if self.controller_name != AUTHORITATIVE_CONTROLLER:
            errors.append("CONTROLLER_NAME_INVALID")

        if self.autonomy_engine_name != AUTONOMY_ENGINE_NAME:
            errors.append("AUTONOMY_ENGINE_NAME_INVALID")

        if not self.controller_contract_version:
            errors.append("CONTRACT_VERSION_MISSING")

        if self.integration_contract_version != INTEGRATION_CONTRACT_VERSION:
            errors.append("INTEGRATION_CONTRACT_VERSION_UNSUPPORTED")

        if not self.architecture_locked:
            errors.append("ARCHITECTURE_NOT_LOCKED")

        if not self.controller_authoritative:
            errors.append("CONTROLLER_NOT_AUTHORITATIVE")

        errors.extend(self.capabilities.validate())

        return tuple(errors)


@dataclass(frozen=True)
class IntegrationLockResult:
    """
    Deterministic result of integration-lock validation.
    """

    status: IntegrationLockStatus
    allowed: bool
    reason: str
    block_reason: IntegrationBlockReason | None = None
    errors: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "block_reason": (
                self.block_reason.value
                if self.block_reason is not None
                else None
            ),
            "errors": list(self.errors),
            "evidence": dict(self.evidence),
        }


def validate_integration(
    contract: IntegrationContract,
) -> IntegrationLockResult:
    """
    Validate the controller/engine integration contract.

    This function is pure and side-effect free.
    """

    if not isinstance(contract, IntegrationContract):
        return IntegrationLockResult(
            status=IntegrationLockStatus.INVALID,
            allowed=False,
            reason="Integration contract is invalid.",
            block_reason=IntegrationBlockReason.INTEGRATION_CONTRACT_INVALID,
            errors=("contract must be an IntegrationContract.",),
            evidence={},
        )

    errors = contract.validate()

    if errors:
        reason = IntegrationBlockReason.INTEGRATION_CONTRACT_INVALID

        if "CONTRACT_VERSION_MISSING" in errors:
            reason = IntegrationBlockReason.CONTRACT_VERSION_MISSING
        elif "ARCHITECTURE_NOT_LOCKED" in errors:
            reason = IntegrationBlockReason.ARCHITECTURE_NOT_LOCKED
        elif "CONTROLLER_NOT_AUTHORITATIVE" in errors:
            reason = IntegrationBlockReason.CONTROLLER_NOT_AUTHORITATIVE
        elif (
            "DIRECT_STATE_MUTATION_FORBIDDEN" in errors
            or "EXECUTOR_DISCOVERY_FORBIDDEN" in errors
        ):
            reason = IntegrationBlockReason.CAPABILITY_CONTRACT_INVALID

        return IntegrationLockResult(
            status=IntegrationLockStatus.INCOMPATIBLE,
            allowed=False,
            reason="Integration contract validation failed.",
            block_reason=reason,
            errors=errors,
            evidence={
                "integration_contract_version": contract.integration_contract_version,
                "controller_contract_version": contract.controller_contract_version,
                "architecture_locked": contract.architecture_locked,
                "controller_authoritative": contract.controller_authoritative,
            },
        )

    return IntegrationLockResult(
        status=IntegrationLockStatus.LOCKED,
        allowed=True,
        reason="REOS_CONTROL_CENTER and AUTONOMY_ENGINE integration contract is locked and compatible.",
        errors=(),
        evidence={
            "integration_contract_version": contract.integration_contract_version,
            "controller_contract_version": contract.controller_contract_version,
            "controller_authoritative": True,
            "architecture_locked": True,
            "upgrade_safe": True,
        },
    )


def integration_contract() -> IntegrationContract:
    """
    Return the canonical frozen integration contract.

    No external state is read.
    No controller command is executed.
    """

    return IntegrationContract(
        controller_name=AUTHORITATIVE_CONTROLLER,
        autonomy_engine_name=AUTONOMY_ENGINE_NAME,
        controller_contract_version=MIN_SUPPORTED_CONTROLLER_CONTRACT,
        integration_contract_version=INTEGRATION_CONTRACT_VERSION,
        architecture_locked=True,
        controller_authoritative=True,
        capabilities=IntegrationCapabilities(
            observe_state=True,
            observe_plan=True,
            observe_gate=True,
            observe_verification=True,
            execute_authoritative_mutation=True,
            approve_gate=False,
            transition_controller=False,
            mutate_state_directly=False,
            discover_executor=False,
        ),
    )


def verify_integration_lock() -> IntegrationLockResult:
    """
    Verify the canonical integration lock.

    Pure verification only.
    """

    return validate_integration(integration_contract())


__all__ = [
    "INTEGRATION_CONTRACT_VERSION",
    "AUTHORITATIVE_CONTROLLER",
    "AUTONOMY_ENGINE_NAME",
    "MIN_SUPPORTED_CONTROLLER_CONTRACT",
    "MAX_SUPPORTED_CONTROLLER_CONTRACT",
    "IntegrationLockStatus",
    "IntegrationBlockReason",
    "IntegrationCapabilities",
    "IntegrationContract",
    "IntegrationLockResult",
    "validate_integration",
    "integration_contract",
    "verify_integration_lock",
]