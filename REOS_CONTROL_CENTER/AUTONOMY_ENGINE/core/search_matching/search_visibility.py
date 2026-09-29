from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Protocol


class VisibilityError(ValueError):
    """Base CORE-005 visibility error."""


class TenantScopeError(VisibilityError):
    """Raised when tenant scope is invalid."""


class VisibilityPolicyError(VisibilityError):
    """Raised when visibility policy is invalid."""


class VisibilityResultError(VisibilityError):
    """Raised when a search result is malformed."""


class VisibilityReason(str, Enum):
    ALLOWED = "ALLOWED"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    LIFECYCLE_BLOCKED = "LIFECYCLE_BLOCKED"
    AVAILABILITY_BLOCKED = "AVAILABILITY_BLOCKED"
    INVENTORY_TYPE_BLOCKED = "INVENTORY_TYPE_BLOCKED"
    MALFORMED_DOCUMENT = "MALFORMED_DOCUMENT"


class SearchDocumentProtocol(Protocol):
    tenant_id: str
    lifecycle: str
    availability: str
    inventory_type: str
    index_key: str


class SearchResultProtocol(Protocol):
    document: SearchDocumentProtocol


def _normalize_text(
    value: str,
    *,
    field_name: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise VisibilityPolicyError(
            f"{field_name} must be a string."
        )

    normalized = value.strip().upper()

    if not normalized:
        raise VisibilityPolicyError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _normalize_set(
    values: Iterable[str],
    *,
    field_name: str,
) -> frozenset[str]:
    if isinstance(
        values,
        (str, bytes),
    ):
        raise VisibilityPolicyError(
            f"{field_name} must be an iterable."
        )

    try:
        normalized = frozenset(
            _normalize_text(
                value,
                field_name=field_name,
            )
            for value in values
        )
    except TypeError as exc:
        raise VisibilityPolicyError(
            f"{field_name} must be iterable."
        ) from exc

    if not normalized:
        raise VisibilityPolicyError(
            f"{field_name} cannot be empty."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class SearchVisibilityPolicy:
    """
    Fail-closed visibility policy.

    Default:
        lifecycle must be ACTIVE.

        BLOCKED / ALLOCATED / SOLD /
        UNAVAILABLE inventory is not exposed.

    RESERVED remains visible because visibility and
    commercial availability are different responsibilities.
    """

    visible_lifecycles: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"ACTIVE"}
        )
    )

    blocked_availability: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "BLOCKED",
                "ALLOCATED",
                "SOLD",
                "UNAVAILABLE",
            }
        )
    )

    blocked_inventory_types: frozenset[str] = field(
        default_factory=frozenset
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "visible_lifecycles",
            _normalize_set(
                self.visible_lifecycles,
                field_name="visible_lifecycles",
            ),
        )

        blocked_availability = frozenset()

        if self.blocked_availability:
            blocked_availability = frozenset(
                _normalize_text(
                    value,
                    field_name="blocked_availability",
                )
                for value
                in self.blocked_availability
            )

        object.__setattr__(
            self,
            "blocked_availability",
            blocked_availability,
        )

        blocked_types = frozenset()

        if self.blocked_inventory_types:
            blocked_types = frozenset(
                _normalize_text(
                    value,
                    field_name="blocked_inventory_types",
                )
                for value
                in self.blocked_inventory_types
            )

        object.__setattr__(
            self,
            "blocked_inventory_types",
            blocked_types,
        )


@dataclass(frozen=True, slots=True)
class VisibilityDecision:
    """
    Immutable decision explaining every visibility boundary.
    """

    allowed: bool
    tenant_allowed: bool
    lifecycle_allowed: bool
    availability_allowed: bool
    inventory_type_allowed: bool
    reason: VisibilityReason
    index_key: str | None = None


def _extract_document(
    result: SearchResultProtocol,
) -> SearchDocumentProtocol:
    if not hasattr(
        result,
        "document",
    ):
        raise VisibilityResultError(
            "search result must expose document."
        )

    document = result.document

    required_fields = (
        "tenant_id",
        "lifecycle",
        "availability",
        "inventory_type",
        "index_key",
    )

    for field_name in required_fields:
        if not hasattr(
            document,
            field_name,
        ):
            raise VisibilityResultError(
                "search document is missing "
                f"{field_name}."
            )

    return document


@dataclass(frozen=True, slots=True)
class TenantVisibilityFilter:
    """
    Mandatory tenant and visibility boundary.

    This layer:
    - never ranks
    - never mutates
    - never owns canonical inventory
    - never changes search order
    - never grants authorization

    It only decides whether a candidate can be exposed.
    """

    tenant_id: str
    policy: SearchVisibilityPolicy = (
        SearchVisibilityPolicy()
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.tenant_id,
            str,
        ):
            raise TenantScopeError(
                "tenant_id must be a string."
            )

        normalized = self.tenant_id.strip()

        if not normalized:
            raise TenantScopeError(
                "tenant_id must be non-empty."
            )

        if not isinstance(
            self.policy,
            SearchVisibilityPolicy,
        ):
            raise VisibilityPolicyError(
                "policy must be SearchVisibilityPolicy."
            )

        object.__setattr__(
            self,
            "tenant_id",
            normalized,
        )

    def decide(
        self,
        result: SearchResultProtocol,
    ) -> VisibilityDecision:
        try:
            document = _extract_document(
                result
            )
        except VisibilityResultError:
            return VisibilityDecision(
                allowed=False,
                tenant_allowed=False,
                lifecycle_allowed=False,
                availability_allowed=False,
                inventory_type_allowed=False,
                reason=(
                    VisibilityReason.MALFORMED_DOCUMENT
                ),
                index_key=None,
            )

        index_key = getattr(
            document,
            "index_key",
            None,
        )

        document_tenant = getattr(
            document,
            "tenant_id",
            None,
        )

        # Security boundary must be evaluated first.
        if document_tenant != self.tenant_id:
            return VisibilityDecision(
                allowed=False,
                tenant_allowed=False,
                lifecycle_allowed=False,
                availability_allowed=False,
                inventory_type_allowed=False,
                reason=(
                    VisibilityReason.TENANT_MISMATCH
                ),
                index_key=index_key,
            )

        lifecycle = str(
            getattr(
                document,
                "lifecycle",
                "",
            )
        ).strip().upper()

        availability = str(
            getattr(
                document,
                "availability",
                "",
            )
        ).strip().upper()

        inventory_type = str(
            getattr(
                document,
                "inventory_type",
                "",
            )
        ).strip().upper()

        if not lifecycle:
            return VisibilityDecision(
                allowed=False,
                tenant_allowed=True,
                lifecycle_allowed=False,
                availability_allowed=False,
                inventory_type_allowed=False,
                reason=(
                    VisibilityReason.MALFORMED_DOCUMENT
                ),
                index_key=index_key,
            )

        if not availability:
            return VisibilityDecision(
                allowed=False,
                tenant_allowed=True,
                lifecycle_allowed=False,
                availability_allowed=False,
                inventory_type_allowed=False,
                reason=(
                    VisibilityReason.MALFORMED_DOCUMENT
                ),
                index_key=index_key,
            )

        lifecycle_allowed = (
            lifecycle
            in self.policy.visible_lifecycles
        )

        availability_allowed = (
            availability
            not in self.policy.blocked_availability
        )

        inventory_type_allowed = (
            inventory_type
            not in self.policy.blocked_inventory_types
        )

        if not lifecycle_allowed:
            return VisibilityDecision(
                allowed=False,
                tenant_allowed=True,
                lifecycle_allowed=False,
                availability_allowed=availability_allowed,
                inventory_type_allowed=(
                    inventory_type_allowed
                ),
                reason=(
                    VisibilityReason.LIFECYCLE_BLOCKED
                ),
                index_key=index_key,
            )

        if not availability_allowed:
            return VisibilityDecision(
                allowed=False,
                tenant_allowed=True,
                lifecycle_allowed=True,
                availability_allowed=False,
                inventory_type_allowed=(
                    inventory_type_allowed
                ),
                reason=(
                    VisibilityReason.AVAILABILITY_BLOCKED
                ),
                index_key=index_key,
            )

        if not inventory_type_allowed:
            return VisibilityDecision(
                allowed=False,
                tenant_allowed=True,
                lifecycle_allowed=True,
                availability_allowed=True,
                inventory_type_allowed=False,
                reason=(
                    VisibilityReason.INVENTORY_TYPE_BLOCKED
                ),
                index_key=index_key,
            )

        return VisibilityDecision(
            allowed=True,
            tenant_allowed=True,
            lifecycle_allowed=True,
            availability_allowed=True,
            inventory_type_allowed=True,
            reason=VisibilityReason.ALLOWED,
            index_key=index_key,
        )

    def is_visible(
        self,
        result: SearchResultProtocol,
    ) -> bool:
        return self.decide(
            result
        ).allowed

    def apply(
        self,
        results: Iterable[
            SearchResultProtocol
        ],
    ) -> tuple[
        SearchResultProtocol,
        ...,
    ]:
        try:
            iterator = iter(results)
        except TypeError as exc:
            raise VisibilityResultError(
                "results must be iterable."
            ) from exc

        visible: list[
            SearchResultProtocol
        ] = []

        for result in iterator:
            decision = self.decide(
                result
            )

            if decision.allowed:
                visible.append(
                    result
                )

        # Visibility never becomes ranking.
        # Existing ordering is preserved exactly.
        return tuple(visible)


__all__ = [
    "SearchVisibilityPolicy",
    "TenantScopeError",
    "TenantVisibilityFilter",
    "VisibilityDecision",
    "VisibilityError",
    "VisibilityPolicyError",
    "VisibilityReason",
    "VisibilityResultError",
]
