from __future__ import annotations

from .commission_acrl_contract import (
    CORE008_ACRL_AUTHORITY,
    CommissionACRLContract,
    FinancialReconstructionRequest,
)


class CommissionACRLValidationError(ValueError):
    """CORE-008 / ACRL contract validation failure."""


def validate_acrl_contract(
    contract: CommissionACRLContract,
) -> None:
    if not isinstance(
        contract,
        CommissionACRLContract,
    ):
        raise CommissionACRLValidationError(
            "invalid CommissionACRLContract"
        )

    if contract.contract_version < 1:
        raise CommissionACRLValidationError(
            "unsupported ACRL contract version"
        )

    if not contract.evidence_discoverable:
        raise CommissionACRLValidationError(
            "financial evidence must remain discoverable"
        )

    if not contract.checkpoint_recovery_compatible:
        raise CommissionACRLValidationError(
            "checkpoint/recovery compatibility is required"
        )

    if contract.autonomous_state_mutation_allowed:
        raise CommissionACRLValidationError(
            "autonomous ACRL state mutation is prohibited"
        )


def validate_reconstruction_request(
    request: FinancialReconstructionRequest,
    contract: CommissionACRLContract,
) -> None:
    validate_acrl_contract(contract)

    if not isinstance(
        request,
        FinancialReconstructionRequest,
    ):
        raise CommissionACRLValidationError(
            "invalid reconstruction request"
        )

    if request.tenant_id != contract.tenant_id:
        raise CommissionACRLValidationError(
            "tenant boundary mismatch"
        )

    if request.commission_id != contract.commission_id:
        raise CommissionACRLValidationError(
            "commission boundary mismatch"
        )

    if not contract.supports(request.subject):
        raise CommissionACRLValidationError(
            "requested financial subject is not supported"
        )

    for reference in request.source_references:
        if reference.authority != CORE008_ACRL_AUTHORITY:
            raise CommissionACRLValidationError(
                "source reference authority is not canonical ACRL"
            )


__all__ = [
    "validate_acrl_contract",
    "validate_reconstruction_request",
]
