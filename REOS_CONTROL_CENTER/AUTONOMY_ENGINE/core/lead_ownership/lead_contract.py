"""
CORE-003 T02 — Lead Contract & Schema

Defines the boundary contract for externally supplied lead data.

This module validates data.
It does not create a second Lead domain or persistence engine.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from .lead import (
    LeadPriority,
    LeadSource,
    LeadSourceType,
    LeadStatus,
    LeadValidationError,
)


class LeadContractError(LeadValidationError):
    """Base lead contract error."""


class LeadSchemaError(LeadContractError):
    """Raised when schema requirements are violated."""


@dataclass(frozen=True, slots=True)
class LeadContract:
    """
    Immutable contract describing the accepted Lead representation.
    """

    schema_name: str = "REOS.CORE-003.LEAD"
    schema_version: int = 1
    required_fields: tuple[str, ...] = (
        "lead_id",
        "tenant_id",
        "customer_id",
        "status",
        "priority",
        "source",
        "metadata",
        "revision",
        "created_at",
        "updated_at",
    )
    allow_additional_fields: bool = False

    def __post_init__(self) -> None:
        if not self.schema_name.strip():
            raise LeadSchemaError("schema_name cannot be empty")

        if self.schema_version < 1:
            raise LeadSchemaError(
                "schema_version must be >= 1"
            )

        normalized = tuple(dict.fromkeys(self.required_fields))

        if len(normalized) != len(self.required_fields):
            raise LeadSchemaError(
                "required_fields cannot contain duplicates"
            )

        object.__setattr__(
            self,
            "required_fields",
            normalized,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "required_fields": self.required_fields,
            "allow_additional_fields": self.allow_additional_fields,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def validate_mapping(
        self,
        payload: Mapping[str, Any],
    ) -> None:
        if not isinstance(payload, Mapping):
            raise LeadSchemaError("Lead payload must be a mapping")

        keys = set(payload)
        required = set(self.required_fields)

        missing = required - keys

        if missing:
            raise LeadSchemaError(
                f"Missing required lead fields: "
                f"{sorted(missing)}"
            )

        if not self.allow_additional_fields:
            extra = keys - required

            if extra:
                raise LeadSchemaError(
                    f"Unknown lead fields: {sorted(extra)}"
                )

        self._validate_types(payload)

    def _validate_types(
        self,
        payload: Mapping[str, Any],
    ) -> None:
        if not isinstance(payload["lead_id"], UUID):
            raise LeadSchemaError("lead_id must be UUID")

        if not isinstance(payload["tenant_id"], UUID):
            raise LeadSchemaError("tenant_id must be UUID")

        if not isinstance(payload["customer_id"], UUID):
            raise LeadSchemaError("customer_id must be UUID")

        if not isinstance(payload["status"], LeadStatus):
            raise LeadSchemaError("status must be LeadStatus")

        if not isinstance(payload["priority"], LeadPriority):
            raise LeadSchemaError("priority must be LeadPriority")

        if not isinstance(payload["source"], LeadSource):
            raise LeadSchemaError("source must be LeadSource")

        if not isinstance(payload["metadata"], Mapping):
            raise LeadSchemaError("metadata must be mapping")

        if not isinstance(payload["revision"], int):
            raise LeadSchemaError("revision must be integer")

        if payload["revision"] < 0:
            raise LeadSchemaError(
                "revision cannot be negative"
            )

    def validate_source(self, source: LeadSource) -> None:
        if not isinstance(source, LeadSource):
            raise LeadSchemaError(
                "source must be LeadSource"
            )

        if not isinstance(source.source_type, LeadSourceType):
            raise LeadSchemaError(
                "source.source_type must be LeadSourceType"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "required_fields": list(self.required_fields),
            "allow_additional_fields": self.allow_additional_fields,
            "fingerprint": self.fingerprint,
        }


DEFAULT_LEAD_CONTRACT = LeadContract()
