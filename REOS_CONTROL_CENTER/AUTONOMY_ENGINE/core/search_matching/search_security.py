"""
CORE-005 / Point 08 — Security & Tenant Boundary.

Owns search-facing security boundaries only.

Responsibilities:
- tenant isolation
- query authorization boundary
- result authorization boundary
- cross-tenant index isolation
- sensitive-field filtering
- IDOR protection
- data leakage prevention
- query-abuse boundary

Does NOT own:
- authentication
- identity provider/session management
- business ownership
- governance engine
- fraud engine
- ranking
- matching
- source-of-truth mutation
- Control Center state

Authorization is supplied as a narrow callback/protocol.
This module does not create a second authorization engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Protocol

from .search_domain import SearchRequest, SearchResultItem
from .search_index_contract import InventoryIndexDocument


class SearchSecurityError(ValueError):
    """Base CORE-005 security-boundary error."""


class SearchTenantIsolationError(
    SearchSecurityError
):
    """Raised for tenant-isolation violations."""


class SearchAuthorizationError(
    SearchSecurityError
):
    """Raised for authorization-boundary violations."""


class SearchDataLeakageError(
    SearchSecurityError
):
    """Raised when sensitive data could be exposed."""


class SearchAbuseBoundaryError(
    SearchSecurityError
):
    """Raised when a query exceeds configured safety bounds."""


class SecurityDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class SecurityDenyReason(str, Enum):
    TENANT_MISMATCH = "TENANT_MISMATCH"
    ACTOR_REQUIRED = "ACTOR_REQUIRED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    IDOR_BLOCKED = "IDOR_BLOCKED"
    SENSITIVE_FIELD = "SENSITIVE_FIELD"
    QUERY_TOO_LONG = "QUERY_TOO_LONG"
    PAGE_SIZE_EXCEEDED = "PAGE_SIZE_EXCEEDED"
    CANDIDATE_LIMIT_EXCEEDED = "CANDIDATE_LIMIT_EXCEEDED"
    MALFORMED_RESULT = "MALFORMED_RESULT"


@dataclass(frozen=True, slots=True)
class SearchSecurityPolicy:
    """
    Explicit search-security limits.

    blocked_payload_fields contain fields that must never be exposed
    to the search consumer, even if present in a derived index payload.
    """

    max_query_length: int = 1_000
    max_page_size: int = 100
    max_candidate_count: int = 10_000

    blocked_payload_fields: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "password",
                "password_hash",
                "access_token",
                "refresh_token",
                "secret",
                "secret_key",
                "api_key",
                "private_key",
                "authorization",
            }
        )
    )

    require_actor_for_authorization: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "max_query_length",
            "max_page_size",
            "max_candidate_count",
        ):
            value = getattr(self, field_name)

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
            ):
                raise SearchSecurityError(
                    f"{field_name} must be a positive integer."
                )

        normalized_fields = frozenset(
            str(field_name).strip().casefold()
            for field_name
            in self.blocked_payload_fields
            if str(field_name).strip()
        )

        object.__setattr__(
            self,
            "blocked_payload_fields",
            normalized_fields,
        )


@dataclass(frozen=True, slots=True)
class SearchAuthorizationContext:
    """
    Minimal authorization context.

    This is not an authentication system.
    """

    tenant_id: str
    actor_id: str | None = None
    attributes: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.tenant_id,
                str,
            )
            or not self.tenant_id.strip()
        ):
            raise SearchTenantIsolationError(
                "tenant_id must be non-empty."
            )

        if self.actor_id is not None:
            if (
                not isinstance(
                    self.actor_id,
                    str,
                )
                or not self.actor_id.strip()
            ):
                raise SearchAuthorizationError(
                    "actor_id must be a non-empty string."
                )

        if not isinstance(
            self.attributes,
            Mapping,
        ):
            raise SearchAuthorizationError(
                "attributes must be a mapping."
            )


class SearchAuthorizationProvider(Protocol):
    """
    Narrow external authorization contract.

    CORE-005 asks the existing authorization system only for
    an allow/deny answer. It does not create authorization policy.
    """

    def authorize_search(
        self,
        context: SearchAuthorizationContext,
        request: SearchRequest,
    ) -> bool:
        ...


class CallableSearchAuthorizationProvider:
    """
    Adapter for an existing authorization policy/function.
    """

    def __init__(
        self,
        callback: Callable[
            [
                SearchAuthorizationContext,
                SearchRequest,
            ],
            bool,
        ],
    ) -> None:
        if not callable(callback):
            raise SearchAuthorizationError(
                "authorization callback must be callable."
            )

        self._callback = callback

    def authorize_search(
        self,
        context: SearchAuthorizationContext,
        request: SearchRequest,
    ) -> bool:
        result = self._callback(
            context,
            request,
        )

        if not isinstance(result, bool):
            raise SearchAuthorizationError(
                "authorization provider must return bool."
            )

        return result


@dataclass(frozen=True, slots=True)
class SearchSecurityDecision:
    decision: SecurityDecision
    reason: str
    tenant_id: str
    actor_id: str | None = None


def _sanitize_payload(
    payload: Mapping[str, Any],
    blocked_fields: frozenset[str],
) -> Mapping[str, Any]:
    sanitized: dict[str, Any] = {}

    for key, value in payload.items():
        if not isinstance(key, str):
            continue

        normalized_key = key.casefold()

        if normalized_key in blocked_fields:
            continue

        sanitized[key] = value

    return sanitized


def sanitize_search_document(
    document: InventoryIndexDocument,
    policy: SearchSecurityPolicy,
) -> InventoryIndexDocument:
    """
    Rebuild one immutable projection with a sanitized payload.

    Source truth is never modified.
    """
    if not isinstance(
        document,
        InventoryIndexDocument,
    ):
        raise SearchDataLeakageError(
            "document must be InventoryIndexDocument."
        )

    blocked = {
        key.casefold()
        for key in document.payload.keys()
        if key.casefold()
        in policy.blocked_payload_fields
    }

    if not blocked:
        return document

    sanitized_payload = _sanitize_payload(
        document.payload,
        policy.blocked_payload_fields,
    )

    return InventoryIndexDocument(
        tenant_id=document.tenant_id,
        project_id=document.project_id,
        inventory_id=document.inventory_id,
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        lifecycle=document.lifecycle,
        availability=document.availability,
        name=document.name,
        inventory_version=document.inventory_version,
        index_key=document.index_key,
        schema_version=document.schema_version,
        index_version=document.index_version,
        index_fingerprint=document.index_fingerprint,
        operation=document.operation,
        payload=sanitized_payload,
    )


@dataclass(slots=True)
class SearchSecurityBoundary:
    """
    Search-facing security boundary.

    Order:
        tenant
        -> query bounds
        -> authorization
        -> result isolation
        -> sensitive-field sanitization
    """

    policy: SearchSecurityPolicy = field(
        default_factory=SearchSecurityPolicy
    )
    authorization_provider: (
        SearchAuthorizationProvider | None
    ) = None

    def validate_request(
        self,
        request: SearchRequest,
        context: SearchAuthorizationContext,
    ) -> SearchSecurityDecision:
        if not isinstance(
            request,
            SearchRequest,
        ):
            raise SearchAuthorizationError(
                "request must be SearchRequest."
            )

        if not isinstance(
            context,
            SearchAuthorizationContext,
        ):
            raise SearchAuthorizationError(
                "context must be SearchAuthorizationContext."
            )

        # First boundary: tenant.
        if (
            request.tenant.tenant_id
            != context.tenant_id
        ):
            return SearchSecurityDecision(
                decision=SecurityDecision.DENY,
                reason=(
                    SecurityDenyReason.TENANT_MISMATCH.value
                ),
                tenant_id=context.tenant_id,
                actor_id=context.actor_id,
            )

        if (
            len(request.query)
            > self.policy.max_query_length
        ):
            return SearchSecurityDecision(
                decision=SecurityDecision.DENY,
                reason=(
                    SecurityDenyReason.QUERY_TOO_LONG.value
                ),
                tenant_id=context.tenant_id,
                actor_id=context.actor_id,
            )

        if (
            request.pagination.page_size
            > self.policy.max_page_size
        ):
            return SearchSecurityDecision(
                decision=SecurityDecision.DENY,
                reason=(
                    SecurityDenyReason.PAGE_SIZE_EXCEEDED.value
                ),
                tenant_id=context.tenant_id,
                actor_id=context.actor_id,
            )

        if (
            self.policy.require_actor_for_authorization
            and not context.actor_id
        ):
            return SearchSecurityDecision(
                decision=SecurityDecision.DENY,
                reason=(
                    SecurityDenyReason.ACTOR_REQUIRED.value
                ),
                tenant_id=context.tenant_id,
                actor_id=context.actor_id,
            )

        if self.authorization_provider is not None:
            allowed = (
                self.authorization_provider.authorize_search(
                    context,
                    request,
                )
            )

            if not allowed:
                return SearchSecurityDecision(
                    decision=SecurityDecision.DENY,
                    reason=(
                        SecurityDenyReason.AUTHORIZATION_DENIED.value
                    ),
                    tenant_id=context.tenant_id,
                    actor_id=context.actor_id,
                )

        return SearchSecurityDecision(
            decision=SecurityDecision.ALLOW,
            reason=SecurityDecision.ALLOW.value,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
        )

    def validate_candidate_count(
        self,
        count: int,
    ) -> None:
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
        ):
            raise SearchAbuseBoundaryError(
                "candidate count must be a non-negative integer."
            )

        if (
            count
            > self.policy.max_candidate_count
        ):
            raise SearchAbuseBoundaryError(
                "candidate count exceeds search abuse boundary."
            )

    def enforce_tenant_result_boundary(
        self,
        context: SearchAuthorizationContext,
        documents: Iterable[
            InventoryIndexDocument
        ],
    ) -> tuple[
        InventoryIndexDocument,
        ...,
    ]:
        if isinstance(
            documents,
            (str, bytes),
        ):
            raise SearchTenantIsolationError(
                "documents must be iterable."
            )

        materialized = list(documents)

        self.validate_candidate_count(
            len(materialized)
        )

        visible: list[
            InventoryIndexDocument
        ] = []

        seen_ids: set[str] = set()

        for document in materialized:
            if not isinstance(
                document,
                InventoryIndexDocument,
            ):
                raise SearchDataLeakageError(
                    "Invalid search document."
                )

            # Explicit IDOR/cross-tenant boundary.
            if (
                document.tenant_id
                != context.tenant_id
            ):
                raise SearchTenantIsolationError(
                    "Cross-tenant search result blocked."
                )

            if document.index_key in seen_ids:
                raise SearchSecurityError(
                    "Duplicate result identity detected."
                )

            seen_ids.add(
                document.index_key
            )

            visible.append(
                sanitize_search_document(
                    document,
                    self.policy,
                )
            )

        return tuple(visible)

    def sanitize_result_items(
        self,
        context: SearchAuthorizationContext,
        items: Iterable[SearchResultItem],
    ) -> tuple[SearchResultItem, ...]:
        if isinstance(
            items,
            (str, bytes),
        ):
            raise SearchDataLeakageError(
                "items must be iterable."
            )

        sanitized: list[SearchResultItem] = []

        for item in items:
            if not isinstance(
                item,
                SearchResultItem,
            ):
                raise SearchDataLeakageError(
                    "Malformed search result item."
                )

            document = item.document

            if (
                document.tenant_id
                != context.tenant_id
            ):
                raise SearchTenantIsolationError(
                    "Cross-tenant result exposure blocked."
                )

            sanitized_document = (
                sanitize_search_document(
                    document,
                    self.policy,
                )
            )

            sanitized.append(
                SearchResultItem(
                    document=sanitized_document,
                    position=item.position,
                    score=item.score,
                    highlights=item.highlights,
                )
            )

        return tuple(sanitized)


__all__ = [
    "SearchSecurityError",
    "SearchTenantIsolationError",
    "SearchAuthorizationError",
    "SearchDataLeakageError",
    "SearchAbuseBoundaryError",
    "SecurityDecision",
    "SecurityDenyReason",
    "SearchSecurityPolicy",
    "SearchAuthorizationContext",
    "SearchAuthorizationProvider",
    "CallableSearchAuthorizationProvider",
    "SearchSecurityDecision",
    "sanitize_search_document",
    "SearchSecurityBoundary",
]
