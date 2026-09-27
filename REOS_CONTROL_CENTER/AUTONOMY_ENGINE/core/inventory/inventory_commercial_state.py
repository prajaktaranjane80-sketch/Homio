"""
CORE-004 T07 — Inventory Attributes & Commercial State

Owns:
- physical attributes
- location attributes
- pricing references
- availability-facing attributes
- commercial metadata
- attribute versioning
- effective dates
- historical truth

Does NOT own:
- inventory identity
- lifecycle transitions
- availability mutation
- pricing engine
- commission engine
- acquisition
- provenance evidence storage
- concurrency coordinator
- authorization
- event transport
- REOS state
- ACRL execution

Pricing is represented by an immutable pricing reference.
CORE-004 does not become a pricing or commission engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class InventoryCommercialStateError(
    ValueError
):
    """Base commercial-state error."""


class CommercialEffectiveDateError(
    InventoryCommercialStateError
):
    """Raised for invalid effective-date ranges."""


class CommercialVersionConflict(
    InventoryCommercialStateError
):
    """Raised for invalid commercial-state versioning."""


class CommercialIntegrityError(
    InventoryCommercialStateError
):
    """Raised when historical truth is violated."""


def _text(
    value: str,
    name: str,
) -> str:
    if not isinstance(value, str):
        raise InventoryCommercialStateError(
            f"{name} must be string."
        )

    value = value.strip()

    if not value:
        raise InventoryCommercialStateError(
            f"{name} cannot be empty."
        )

    return value


def _aware_time(
    value: datetime,
    name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise InventoryCommercialStateError(
            f"{name} must be datetime."
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise InventoryCommercialStateError(
            f"{name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _money(
    value: Decimal | int | str,
    name: str,
) -> Decimal:
    try:
        decimal_value = (
            value
            if isinstance(value, Decimal)
            else Decimal(str(value))
        )
    except Exception as exc:
        raise InventoryCommercialStateError(
            f"{name} must be decimal-compatible."
        ) from exc

    if decimal_value.is_nan() or decimal_value.is_infinite():
        raise InventoryCommercialStateError(
            f"{name} must be finite."
        )

    if decimal_value < 0:
        raise InventoryCommercialStateError(
            f"{name} cannot be negative."
        )

    return decimal_value


def _canonicalize(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Decimal,
    ):
        return format(
            value,
            "f",
        )

    if isinstance(
        value,
        datetime,
    ):
        return _aware_time(
            value,
            "datetime",
        ).isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _canonicalize(item)
            for item in value
        ]

    if (
        value is None
        or isinstance(
            value,
            (str, int, float, bool),
        )
    ):
        return value

    raise InventoryCommercialStateError(
        "Unsupported commercial-state value type: "
        f"{type(value).__name__}"
    )


def _fingerprint(
    payload: Mapping[str, Any],
) -> str:
    canonical = json.dumps(
        _canonicalize(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class PhysicalAttributes:
    """
    Physical inventory facts.

    Facts are descriptive; they do not mutate inventory identity.
    """

    area_value: Decimal | None = None
    area_unit: str | None = None
    bedrooms: int | None = None
    bathrooms: Decimal | None = None
    floor: int | None = None
    facing: str | None = None
    parking_count: int | None = None

    def __post_init__(self) -> None:
        if self.area_value is not None:
            object.__setattr__(
                self,
                "area_value",
                _money(
                    self.area_value,
                    "area_value",
                ),
            )

        if self.area_unit is not None:
            object.__setattr__(
                self,
                "area_unit",
                _text(
                    self.area_unit,
                    "area_unit",
                ),
            )

        for field_name in (
            "bedrooms",
            "floor",
            "parking_count",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is not None:
                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                ):
                    raise InventoryCommercialStateError(
                        f"{field_name} must be integer."
                    )

                if value < 0:
                    raise InventoryCommercialStateError(
                        f"{field_name} cannot be negative."
                    )

        if self.bathrooms is not None:
            object.__setattr__(
                self,
                "bathrooms",
                _money(
                    self.bathrooms,
                    "bathrooms",
                ),
            )

        if self.facing is not None:
            object.__setattr__(
                self,
                "facing",
                _text(
                    self.facing,
                    "facing",
                ),
            )


@dataclass(frozen=True, slots=True)
class LocationAttributes:
    country_code: str
    region: str
    city: str
    locality: str | None = None
    postal_code: str | None = None
    address_line: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    def __post_init__(self) -> None:
        country = _text(
            self.country_code,
            "country_code",
        ).upper()

        if len(country) != 2 or not country.isalpha():
            raise InventoryCommercialStateError(
                "country_code must be ISO-3166 alpha-2."
            )

        object.__setattr__(
            self,
            "country_code",
            country,
        )

        object.__setattr__(
            self,
            "region",
            _text(
                self.region,
                "region",
            ),
        )

        object.__setattr__(
            self,
            "city",
            _text(
                self.city,
                "city",
            ),
        )

        for field_name in (
            "locality",
            "postal_code",
            "address_line",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _text(
                        value,
                        field_name,
                    ),
                )

        if self.latitude is not None:
            latitude = Decimal(
                str(self.latitude)
            )

            if latitude < -90 or latitude > 90:
                raise InventoryCommercialStateError(
                    "latitude must be between -90 and 90."
                )

            object.__setattr__(
                self,
                "latitude",
                latitude,
            )

        if self.longitude is not None:
            longitude = Decimal(
                str(self.longitude)
            )

            if longitude < -180 or longitude > 180:
                raise InventoryCommercialStateError(
                    "longitude must be between -180 and 180."
                )

            object.__setattr__(
                self,
                "longitude",
                longitude,
            )


@dataclass(frozen=True, slots=True)
class PricingReference:
    """
    Reference to pricing truth owned by a commercial/pricing subsystem.

    No pricing calculation is performed here.
    """

    pricing_reference: str
    currency: str
    amount: Decimal
    price_type: str
    external_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "pricing_reference",
            _text(
                self.pricing_reference,
                "pricing_reference",
            ),
        )

        currency = _text(
            self.currency,
            "currency",
        ).upper()

        if len(currency) != 3:
            raise InventoryCommercialStateError(
                "currency must be ISO-4217 style 3-letter code."
            )

        object.__setattr__(
            self,
            "currency",
            currency,
        )

        object.__setattr__(
            self,
            "amount",
            _money(
                self.amount,
                "amount",
            ),
        )

        object.__setattr__(
            self,
            "price_type",
            _text(
                self.price_type,
                "price_type",
            ),
        )

        if self.external_version is not None:
            object.__setattr__(
                self,
                "external_version",
                _text(
                    self.external_version,
                    "external_version",
                ),
            )


@dataclass(frozen=True, slots=True)
class CommercialStateSnapshot:
    """
    Immutable commercial/attribute state effective for a defined period.
    """

    inventory_id: str
    tenant_id: str
    version: int
    physical: PhysicalAttributes | None
    location: LocationAttributes | None
    pricing: PricingReference | None
    availability_attributes: Mapping[str, Any]
    commercial_metadata: Mapping[str, Any]
    effective_from: datetime
    effective_to: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        if (
            not isinstance(
                self.version,
                int,
            )
            or self.version < 1
        ):
            raise CommercialVersionConflict(
                "commercial state version must be >= 1."
            )

        if self.physical is not None:
            if not isinstance(
                self.physical,
                PhysicalAttributes,
            ):
                raise InventoryCommercialStateError(
                    "physical must be PhysicalAttributes."
                )

        if self.location is not None:
            if not isinstance(
                self.location,
                LocationAttributes,
            ):
                raise InventoryCommercialStateError(
                    "location must be LocationAttributes."
                )

        if self.pricing is not None:
            if not isinstance(
                self.pricing,
                PricingReference,
            ):
                raise InventoryCommercialStateError(
                    "pricing must be PricingReference."
                )

        if not isinstance(
            self.availability_attributes,
            Mapping,
        ):
            raise InventoryCommercialStateError(
                "availability_attributes must be mapping."
            )

        if not isinstance(
            self.commercial_metadata,
            Mapping,
        ):
            raise InventoryCommercialStateError(
                "commercial_metadata must be mapping."
            )

        object.__setattr__(
            self,
            "effective_from",
            _aware_time(
                self.effective_from,
                "effective_from",
            ),
        )

        if self.effective_to is not None:
            object.__setattr__(
                self,
                "effective_to",
                _aware_time(
                    self.effective_to,
                    "effective_to",
                ),
            )

            if (
                self.effective_to
                <= self.effective_from
            ):
                raise CommercialEffectiveDateError(
                    "effective_to must be after effective_from."
                )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            self.to_dict(
                include_fingerprint=False
            )
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "version": self.version,
            "physical": _canonicalize(
                self.physical.__dict__
                if self.physical is not None
                else None
            ),
            "location": _canonicalize(
                self.location.__dict__
                if self.location is not None
                else None
            ),
            "pricing": _canonicalize(
                self.pricing.__dict__
                if self.pricing is not None
                else None
            ),
            "availability_attributes": (
                _canonicalize(
                    self.availability_attributes
                )
            ),
            "commercial_metadata": (
                _canonicalize(
                    self.commercial_metadata
                )
            ),
            "effective_from": (
                self.effective_from.isoformat()
            ),
            "effective_to": (
                self.effective_to.isoformat()
                if self.effective_to is not None
                else None
            ),
        }

        if include_fingerprint:
            payload["fingerprint"] = (
                self.fingerprint
            )

        return payload


def validate_historical_truth(
    history: tuple[
        CommercialStateSnapshot,
        ...
    ],
) -> None:
    """
    Validate monotonic commercial-state versions and non-overlapping
    effective periods.
    """
    previous_version: int | None = None
    previous_end: datetime | None = None
    inventory_id: str | None = None
    tenant_id: str | None = None

    ordered = tuple(
        sorted(
            history,
            key=lambda item: (
                item.effective_from,
                item.version,
            ),
        )
    )

    for snapshot in ordered:
        if inventory_id is None:
            inventory_id = snapshot.inventory_id
        elif inventory_id != snapshot.inventory_id:
            raise CommercialIntegrityError(
                "Commercial history mixes inventories."
            )

        if tenant_id is None:
            tenant_id = snapshot.tenant_id
        elif tenant_id != snapshot.tenant_id:
            raise CommercialIntegrityError(
                "Commercial history crosses tenants."
            )

        if previous_version is not None:
            if snapshot.version != previous_version + 1:
                raise CommercialVersionConflict(
                    "Commercial history version gap."
                )

        if (
            previous_end is not None
            and snapshot.effective_from < previous_end
        ):
            raise CommercialEffectiveDateError(
                "Commercial effective periods overlap."
            )

        previous_version = snapshot.version
        previous_end = snapshot.effective_to


__all__ = [
    "InventoryCommercialStateError",
    "CommercialEffectiveDateError",
    "CommercialVersionConflict",
    "CommercialIntegrityError",
    "PhysicalAttributes",
    "LocationAttributes",
    "PricingReference",
    "CommercialStateSnapshot",
    "validate_historical_truth",
]
