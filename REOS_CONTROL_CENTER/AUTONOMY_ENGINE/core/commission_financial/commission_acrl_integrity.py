from __future__ import annotations

from dataclasses import dataclass

from .commission_acrl_contract import (
    CommissionACRLContract,
    FinancialReconstructionRequest,
)
from .commission_acrl_reconstruction import (
    FinancialReconstructionResult,
)
from .commission_acrl_validation import (
    validate_acrl_contract,
    validate_reconstruction_request,
)


class CommissionACRLIntegrityError(ValueError):
    """CORE-008 ACRL integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionACRLIntegrityReport:
    valid: bool
    tenant_id: str
    commission_id: str
    subject: str
    reconstruction_verified: bool
    contract_verified: bool
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "subject": self.subject,
            "reconstruction_verified": (
                self.reconstruction_verified
            ),
            "contract_verified": self.contract_verified,
            "reason": self.reason,
        }


def inspect_acrl_integrity(
    contract: CommissionACRLContract,
    request: FinancialReconstructionRequest,
    result: FinancialReconstructionResult,
) -> CommissionACRLIntegrityReport:
    try:
        validate_acrl_contract(contract)
        validate_reconstruction_request(
            request,
            contract,
        )

        if result.request != request:
            raise CommissionACRLIntegrityError(
                "reconstruction result does not match request"
            )

        reconstruction_verified = result.verify()

        if not reconstruction_verified:
            raise CommissionACRLIntegrityError(
                "reconstruction fingerprint verification failed"
            )

        return CommissionACRLIntegrityReport(
            valid=True,
            tenant_id=request.tenant_id,
            commission_id=request.commission_id,
            subject=request.subject.value,
            reconstruction_verified=True,
            contract_verified=True,
        )

    except Exception as exc:
        return CommissionACRLIntegrityReport(
            valid=False,
            tenant_id=request.tenant_id,
            commission_id=request.commission_id,
            subject=request.subject.value,
            reconstruction_verified=False,
            contract_verified=False,
            reason=str(exc),
        )


def assert_acrl_integrity(
    contract: CommissionACRLContract,
    request: FinancialReconstructionRequest,
    result: FinancialReconstructionResult,
) -> None:
    report = inspect_acrl_integrity(
        contract,
        request,
        result,
    )

    if not report.valid:
        raise CommissionACRLIntegrityError(
            report.reason
        )


__all__ = [
    "CommissionACRLIntegrityError",
    "CommissionACRLIntegrityReport",
    "inspect_acrl_integrity",
    "assert_acrl_integrity",
]
