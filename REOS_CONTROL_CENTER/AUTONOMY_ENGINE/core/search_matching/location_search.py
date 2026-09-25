from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, isfinite, radians, sin, sqrt
from typing import Iterable

from .inventory_indexing import InventoryIndexDocument


class LocationSearchError(ValueError):
    """Base error for location search."""


class InvalidGeoPointError(LocationSearchError):
    """Invalid latitude/longitude."""


class InvalidLocationRadiusError(LocationSearchError):
    """Invalid search radius."""


class LocationSearchTenantError(LocationSearchError):
    """Invalid tenant scope."""


def _tenant(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LocationSearchTenantError("tenant_id must be a non-empty string.")
    return value.strip()


def _coordinate(
    value: float,
    *,
    name: str,
    minimum: float,
    maximum: float,
) -> float:
    if isinstance(value, bool):
        raise InvalidGeoPointError(f"{name} must be numeric.")

    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidGeoPointError(f"{name} must be numeric.") from exc

    if not isfinite(value):
        raise InvalidGeoPointError(f"{name} must be finite.")

    if not minimum <= value <= maximum:
        raise InvalidGeoPointError(
            f"{name} must be between {minimum} and {maximum}."
        )

    return value


@dataclass(frozen=True)
class GeoPoint:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "latitude",
            _coordinate(
                self.latitude,
                name="latitude",
                minimum=-90.0,
                maximum=90.0,
            ),
        )
        object.__setattr__(
            self,
            "longitude",
            _coordinate(
                self.longitude,
                name="longitude",
                minimum=-180.0,
                maximum=180.0,
            ),
        )


@dataclass(frozen=True)
class LocationSearchDocument:
    document: InventoryIndexDocument
    point: GeoPoint

    @property
    def tenant_id(self) -> str:
        return self.document.tenant_id

    @property
    def index_key(self) -> str:
        return self.document.index_key


@dataclass(frozen=True)
class LocationSearchResult:
    document: InventoryIndexDocument
    distance_km: float

    @property
    def inventory_code(self) -> str:
        return self.document.inventory_code

    @property
    def inventory_id(self) -> str:
        return self.document.inventory_id

    @property
    def tenant_id(self) -> str:
        return self.document.tenant_id


def haversine_distance_km(
    origin: GeoPoint,
    target: GeoPoint,
) -> float:
    earth_radius_km = 6371.0088

    lat1 = radians(origin.latitude)
    lat2 = radians(target.latitude)
    delta_lat = radians(target.latitude - origin.latitude)
    delta_lon = radians(target.longitude - origin.longitude)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    a = max(0.0, min(1.0, a))

    return 2.0 * earth_radius_km * asin(sqrt(a))


@dataclass(frozen=True)
class LocationSearchFilter:
    tenant_id: str
    origin: GeoPoint
    radius_km: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _tenant(self.tenant_id),
        )

        if isinstance(self.radius_km, bool):
            raise InvalidLocationRadiusError(
                "radius_km must be positive and finite."
            )

        try:
            radius = float(self.radius_km)
        except (TypeError, ValueError) as exc:
            raise InvalidLocationRadiusError(
                "radius_km must be positive and finite."
            ) from exc

        if not isfinite(radius) or radius <= 0:
            raise InvalidLocationRadiusError(
                "radius_km must be positive and finite."
            )

        object.__setattr__(self, "radius_km", radius)

    def apply(
        self,
        documents: Iterable[LocationSearchDocument],
    ) -> tuple[LocationSearchResult, ...]:
        results: list[LocationSearchResult] = []

        for item in documents:
            if item.tenant_id != self.tenant_id:
                continue

            distance = haversine_distance_km(
                self.origin,
                item.point,
            )

            if distance <= self.radius_km:
                results.append(
                    LocationSearchResult(
                        document=item.document,
                        distance_km=distance,
                    )
                )

        results.sort(
            key=lambda item: (
                item.distance_km,
                item.document.index_key.casefold(),
            )
        )

        return tuple(results)


__all__ = [
    "GeoPoint",
    "InvalidGeoPointError",
    "InvalidLocationRadiusError",
    "LocationSearchDocument",
    "LocationSearchError",
    "LocationSearchFilter",
    "LocationSearchResult",
    "LocationSearchTenantError",
    "haversine_distance_km",
]
