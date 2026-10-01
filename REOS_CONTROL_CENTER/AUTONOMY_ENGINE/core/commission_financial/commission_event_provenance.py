from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .commission_event_contract import (
    CORE008_EVENT_SCHEMA,
    CommissionEventType,
)


@dataclass(frozen=True, slots=True)
class CommissionFinancialEventProvenance:
    tenant_reference: str
    commission_id: str
    event_type: CommissionEventType
    source_type: str
    source_id: str
    source_fingerprint: str
    parent_event_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "tenant_reference",
            "commission_id",
            "source_type",
            "source_id",
            "source_fingerprint",
        ):
            value = getattr(self, name)

            if not isinstance(
                value,
                str,
            ) or not value.strip():
                raise ValueError(
                    f"{name} cannot be empty"
                )

            object.__setattr__(
                self,
                name,
                value.strip(),
            )

        if not isinstance(
            self.event_type,
            CommissionEventType,
        ):
            raise TypeError(
                "event_type must be CommissionEventType"
            )

        if self.parent_event_id is not None:
            if (
                not isinstance(
                    self.parent_event_id,
                    str,
                )
                or not self.parent_event_id.strip()
            ):
                raise ValueError(
                    "parent_event_id cannot be empty"
                )

            object.__setattr__(
                self,
                "parent_event_id",
                self.parent_event_id.strip(),
            )

    @property
    def fingerprint(self) -> str:
        material = {
            "schema": CORE008_EVENT_SCHEMA,
            "tenant_reference": self.tenant_reference,
            "commission_id": self.commission_id,
            "event_type": self.event_type.value,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_fingerprint": self.source_fingerprint,
            "parent_event_id": self.parent_event_id,
        }

        return sha256(
            json.dumps(
                material,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, str | None]:
        return {
            "schema": CORE008_EVENT_SCHEMA,
            "tenant_reference": self.tenant_reference,
            "commission_id": self.commission_id,
            "event_type": self.event_type.value,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_fingerprint": self.source_fingerprint,
            "parent_event_id": self.parent_event_id,
            "provenance_fingerprint": self.fingerprint,
        }


__all__ = [
    "CommissionFinancialEventProvenance",
]
