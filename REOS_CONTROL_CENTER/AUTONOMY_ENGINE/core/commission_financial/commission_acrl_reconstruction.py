from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Mapping

from .commission_acrl_contract import (
    ACRLSourceReference,
    CommissionACRLValidationError,
    FinancialReconstructionRequest,
    FinancialReconstructionSubject,
)


class CommissionACRLReconstructionError(RuntimeError):
    """CORE-008 ACRL reconstruction integration error."""


def _calculate_result_fingerprint(
    request: FinancialReconstructionRequest,
    reconstructed_state: Mapping[str, Any],
    source_references: tuple[ACRLSourceReference, ...],
) -> str:
    material = {
        "tenant_id": request.tenant_id,
        "commission_id": request.commission_id,
        "subject": request.subject.value,
        "sources": [
            reference.to_dict()
            for reference in sorted(
                source_references,
                key=lambda item: (
                    item.source_kind,
                    item.source_id,
                    item.fingerprint,
                ),
            )
        ],
        "state": dict(reconstructed_state),
    }

    canonical = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return sha256(
        canonical.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class FinancialReconstructionResult:
    """
    Immutable reconstruction result returned by the existing ACRL authority.

    CORE-008 does not reconstruct data itself.
    """

    request: FinancialReconstructionRequest
    reconstructed_state: Mapping[str, Any]
    result_fingerprint: str
    source_references: tuple[ACRLSourceReference, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.reconstructed_state,
            Mapping,
        ):
            raise CommissionACRLValidationError(
                "reconstructed_state must be a mapping"
            )

        object.__setattr__(
            self,
            "reconstructed_state",
            dict(self.reconstructed_state),
        )

        references = tuple(self.source_references)

        if not references:
            raise CommissionACRLValidationError(
                "reconstruction requires source references"
            )

        object.__setattr__(
            self,
            "source_references",
            references,
        )

        if not isinstance(
            self.result_fingerprint,
            str,
        ) or not self.result_fingerprint.strip():
            raise CommissionACRLValidationError(
                "result_fingerprint cannot be empty"
            )

    @property
    def deterministic_material(self) -> dict[str, Any]:
        return {
            "tenant_id": self.request.tenant_id,
            "commission_id": self.request.commission_id,
            "subject": self.request.subject.value,
            "sources": [
                reference.to_dict()
                for reference in sorted(
                    self.source_references,
                    key=lambda item: (
                        item.source_kind,
                        item.source_id,
                        item.fingerprint,
                    ),
                )
            ],
            "state": self.reconstructed_state,
        }

    @property
    def deterministic_fingerprint(self) -> str:
        return _calculate_result_fingerprint(
            self.request,
            self.reconstructed_state,
            self.source_references,
        )

    def verify(self) -> bool:
        return (
            self.result_fingerprint
            == self.deterministic_fingerprint
        )


class CommissionACRLReconstructor:
    """
    Adapter contract for the existing ACRL reconstruction authority.

    The supplied callback must point to the existing ACRL reconstruction
    implementation. This class does not create another reconstruction engine.
    """

    def __init__(
        self,
        reconstruct: Callable[
            [FinancialReconstructionRequest],
            Mapping[str, Any],
        ],
    ) -> None:
        if not callable(reconstruct):
            raise TypeError(
                "reconstruct must be callable"
            )

        self._reconstruct = reconstruct

    def reconstruct(
        self,
        request: FinancialReconstructionRequest,
    ) -> FinancialReconstructionResult:
        if not isinstance(
            request,
            FinancialReconstructionRequest,
        ):
            raise TypeError(
                "request must be FinancialReconstructionRequest"
            )

        state = self._reconstruct(request)

        if not isinstance(state, Mapping):
            raise CommissionACRLReconstructionError(
                "ACRL reconstruction must return a mapping"
            )

        normalized = dict(state)

        reference_map = {
            reference.source_id: reference
            for reference in request.source_references
        }

        source_references = tuple(
            reference_map.values()
        )

        result_fingerprint = _calculate_result_fingerprint(
            request,
            normalized,
            source_references,
        )

        return FinancialReconstructionResult(
            request=request,
            reconstructed_state=normalized,
            result_fingerprint=result_fingerprint,
            source_references=source_references,
        )


def build_reconstruction_request(
    *,
    tenant_id: str,
    commission_id: str,
    subject: FinancialReconstructionSubject,
    source_references: tuple[ACRLSourceReference, ...],
    target_fingerprint: str | None = None,
) -> FinancialReconstructionRequest:
    return FinancialReconstructionRequest(
        tenant_id=tenant_id,
        commission_id=commission_id,
        subject=subject,
        source_references=source_references,
        target_fingerprint=target_fingerprint,
    )


__all__ = [
    "CommissionACRLReconstructor",
    "CommissionACRLReconstructionError",
    "FinancialReconstructionResult",
    "build_reconstruction_request",
]
