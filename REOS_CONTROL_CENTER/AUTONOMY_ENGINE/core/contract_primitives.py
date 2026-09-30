"""Shared mechanical contract primitives for REOS bounded cores."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any
from uuid import UUID


class ContractPrimitiveError(ValueError):
    """Invalid cross-core contract value."""


def deep_freeze(
    value: Any,
    *,
    field_name: str = "value",
) -> Any:
    """Recursively freeze mappings and sequences."""
    if isinstance(value, Mapping):
        frozen = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractPrimitiveError(
                    f"{field_name} mapping keys must be strings."
                )

            frozen[key] = deep_freeze(
                item,
                field_name=f"{field_name}[{key!r}]",
            )

        return MappingProxyType(frozen)

    if isinstance(value, (list, tuple)):
        return tuple(
            deep_freeze(
                item,
                field_name=f"{field_name}[{index}]",
            )
            for index, item in enumerate(value)
        )

    if isinstance(value, (set, frozenset)):
        raise ContractPrimitiveError(
            f"{field_name} cannot contain sets."
        )

    if isinstance(
        value,
        (str, int, float, bool, UUID, datetime, date, Enum),
    ) or value is None:
        return value

    raise ContractPrimitiveError(
        f"{field_name} contains unsupported type "
        f"{type(value).__name__}."
    )


def canonicalize(value: Any) -> Any:
    """Convert contract data to deterministic JSON-compatible form."""
    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ContractPrimitiveError(
                "datetime must be timezone-aware."
            )

        return value.astimezone(timezone.utc).isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if isinstance(value, Mapping):
        return {
            str(key): canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (list, tuple)):
        return [
            canonicalize(item)
            for item in value
        ]

    if isinstance(
        value,
        (str, int, float, bool),
    ) or value is None:
        return value

    raise ContractPrimitiveError(
        f"Unsupported canonical type: {type(value).__name__}."
    )


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def fingerprint(value: Any) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def require_positive_version(
    value: int,
    *,
    field_name: str = "version",
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise ContractPrimitiveError(
            f"{field_name} must be a positive integer."
        )

    return value


def require_same_scope(
    expected_scope: Any,
    actual_scope: Any,
    *,
    field_name: str = "tenant_id",
) -> None:
    if expected_scope != actual_scope:
        raise ContractPrimitiveError(
            f"{field_name} scope mismatch."
        )


__all__ = [
    "ContractPrimitiveError",
    "canonical_json",
    "canonicalize",
    "deep_freeze",
    "fingerprint",
    "require_positive_version",
    "require_same_scope",
]