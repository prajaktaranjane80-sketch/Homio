from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .commission_acrl_contract import (
    CORE008_ACRL_AUTHORITY,
    FinancialReconstructionSubject,
)


class CommissionACRLProvenanceError(ValueError):
    """CORE-008 ACRL provenance error."""


@dataclass(frozen=True, slots=True)
class CommissionACRLProvenance:
    tenant_id: str
    commission_id: str
    subject: FinancialReconstructionSubject
    reconstruction_reference: str
    checkpoint_reference: str | None = None
    recovery_reference: str | None = None
    authority: str = CORE008_ACRL_AUTHORITY

    def __post_init__(self) -> None:
        for name, value in (
            ("tenant_id", self.tenant_id),
            ("commission_id", self.commission_id),
            ("reconstruction_reference", self.reconstruction_reference),
            ("authority", self.authority),
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommissionACRLProvenanceError(
                    f"{name} cannot be empty"
                )

            object.__setattr__(
                self,
                name,
                value.strip(),
            )

        if not isinstance(
            self.subject,
            FinancialReconstructionSubject,
        ):
            raise CommissionACRLProvenanceError(
                "subject is invalid"
            )

        for name, value in (
            ("checkpoint_reference", self.checkpoint_reference),
            ("recovery_reference", self.recovery_reference),
        ):
            if value is not None:
                if (
                    not isinstance(value, str)
                    or not value.strip()
                ):
                    raise CommissionACRLProvenanceError(
                        f"{name} cannot be empty"
                    )

                object.__setattr__(
                    self,
                    name,
                    value.strip(),
                )

    @property
    def fingerprint(self) -> str:
        material = {
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "subject": self.subject.value,
            "reconstruction_reference": (
                self.reconstruction_reference
            ),
            "checkpoint_reference": (
                self.checkpoint_reference
            ),
            "recovery_reference": (
                self.recovery_reference
            ),
            "authority": self.authority,
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

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "subject": self.subject.value,
            "reconstruction_reference": (
                self.reconstruction_reference
            ),
            "checkpoint_reference": (
                self.checkpoint_reference
            ),
            "recovery_reference": (
                self.recovery_reference
            ),
            "authority": self.authority,
            "fingerprint": self.fingerprint,
        }


__all__ = [
    "CommissionACRLProvenance",
    "CommissionACRLProvenanceError",
]
