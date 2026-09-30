from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_contract import CommissionContract


@dataclass(frozen=True, slots=True)
class CommissionTermComparison:
    """Deterministic comparison of two commission-term snapshots."""

    identical: bool
    same_identity: bool
    same_version: bool
    same_terms: bool
    left_fingerprint: str
    right_fingerprint: str

    def __post_init__(self) -> None:
        expected = (
            self.same_identity
            and self.same_version
            and self.same_terms
        )

        if self.identical != expected:
            raise ValueError(
                "identical is inconsistent with comparison fields."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "identical": self.identical,
            "same_identity": self.same_identity,
            "same_version": self.same_version,
            "same_terms": self.same_terms,
            "left_fingerprint": self.left_fingerprint,
            "right_fingerprint": self.right_fingerprint,
        }


def canonical_commission_terms(
    contract: CommissionContract,
) -> dict[str, Any]:
    """Return only immutable contractual terms.

    Runtime execution state is deliberately excluded.
    """

    payload = contract.to_dict(
        include_fingerprint=False
    )

    payload.pop(
        "state",
        None,
    )

    payload.pop(
        "metadata",
        None,
    )

    return payload


def commission_terms_fingerprint(
    contract: CommissionContract,
) -> str:
    return fingerprint(
        canonical_commission_terms(
            contract
        )
    )


def compare_commission_terms(
    left: CommissionContract,
    right: CommissionContract,
) -> CommissionTermComparison:
    if not isinstance(
        left,
        CommissionContract,
    ):
        raise TypeError(
            "left must be CommissionContract."
        )

    if not isinstance(
        right,
        CommissionContract,
    ):
        raise TypeError(
            "right must be CommissionContract."
        )

    left_fingerprint = (
        commission_terms_fingerprint(left)
    )

    right_fingerprint = (
        commission_terms_fingerprint(right)
    )

    return CommissionTermComparison(
        identical=(
            left.identity_key == right.identity_key
            and left.contract_version
            == right.contract_version
            and left_fingerprint
            == right_fingerprint
        ),
        same_identity=(
            left.identity_key
            == right.identity_key
        ),
        same_version=(
            left.contract_version
            == right.contract_version
        ),
        same_terms=(
            left_fingerprint
            == right_fingerprint
        ),
        left_fingerprint=left_fingerprint,
        right_fingerprint=right_fingerprint,
    )


__all__ = [
    "CommissionTermComparison",
    "canonical_commission_terms",
    "commission_terms_fingerprint",
    "compare_commission_terms",
]
