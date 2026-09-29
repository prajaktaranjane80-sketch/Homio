"""
CORE-005 / Point 03 — Projection & Synchronization.

Owns the boundary between canonical source events and the
derived search projection.

Responsibilities:
- source event consumption contract
- projection update contract
- source/projection version tracking
- synchronization boundary
- eventual-consistency state
- stale projection detection
- duplicate event handling
- out-of-order event handling
- deterministic reindex handoff
- no source-of-truth ownership

This module does NOT:
- become an event bus
- mutate CORE-004 Inventory
- become a search backend
- own Qdrant
- own ranking
- own matching
- own Control Center state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Protocol

from ..inventory.inventory import Inventory
from .search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
    build_inventory_index,
    build_inventory_index_delete,
)


class ProjectionSyncError(ValueError):
    """Base projection synchronization error."""


class ProjectionTenantError(ProjectionSyncError):
    """Raised for tenant-boundary violations."""


class ProjectionVersionError(ProjectionSyncError):
    """Raised for invalid source/projection versions."""


class ProjectionEventError(ProjectionSyncError):
    """Raised for malformed projection events."""


class ProjectionApplyStatus(str, Enum):
    """Result of projection-event consumption."""

    APPLIED = "APPLIED"
    DUPLICATE = "DUPLICATE"
    STALE = "STALE"
    CONFLICT = "CONFLICT"


class ProjectionOperation(str, Enum):
    """Source-to-projection operation."""

    UPSERT = "UPSERT"
    DELETE = "DELETE"


@dataclass(frozen=True, slots=True)
class SearchSourceEvent:
    """
    Immutable source event contract.

    The inventory field is a source snapshot reference for
    deterministic projection reconstruction. It is never modified.
    """

    event_id: str
    tenant_id: str
    inventory: Inventory
    source_version: int
    operation: ProjectionOperation
    occurred_at: datetime

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.event_id,
                str,
            )
            or not self.event_id.strip()
        ):
            raise ProjectionEventError(
                "event_id must be a non-empty string."
            )

        if (
            not isinstance(
                self.tenant_id,
                str,
            )
            or not self.tenant_id.strip()
        ):
            raise ProjectionTenantError(
                "tenant_id must be a non-empty string."
            )

        if not isinstance(
            self.inventory,
            Inventory,
        ):
            raise ProjectionEventError(
                "inventory must be CORE-004 Inventory."
            )

        if (
            isinstance(
                self.source_version,
                bool,
            )
            or not isinstance(
                self.source_version,
                int,
            )
            or self.source_version < 1
        ):
            raise ProjectionVersionError(
                "source_version must be a positive integer."
            )

        if (
            self.source_version
            != self.inventory.version
        ):
            raise ProjectionVersionError(
                "source_version must exactly match "
                "inventory.version."
            )

        try:
            operation = ProjectionOperation(
                self.operation
            )
        except (TypeError, ValueError) as exc:
            raise ProjectionEventError(
                "operation must be UPSERT or DELETE."
            ) from exc

        object.__setattr__(
            self,
            "operation",
            operation,
        )

        if not isinstance(
            self.occurred_at,
            datetime,
        ):
            raise ProjectionEventError(
                "occurred_at must be datetime."
            )

        if self.occurred_at.tzinfo is None:
            raise ProjectionEventError(
                "occurred_at must be timezone-aware."
            )


@dataclass(frozen=True, slots=True)
class ProjectionVersion:
    """
    Derived synchronization state.

    This is projection metadata only.
    It never becomes business/source truth.
    """

    tenant_id: str
    index_key: str
    source_version: int
    projection_version: int
    last_event_id: str

    @property
    def is_current(self) -> bool:
        return (
            self.projection_version
            >= self.source_version
        )

    @property
    def is_lagging(self) -> bool:
        return (
            self.projection_version
            < self.source_version
        )


@dataclass(frozen=True, slots=True)
class ProjectionChange:
    """
    Result of one synchronization decision.
    """

    status: ProjectionApplyStatus
    event_id: str
    tenant_id: str
    index_key: str
    source_version: int
    document: InventoryIndexDocument | None
    reason: str


class SearchProjectionSink(Protocol):
    """
    Runtime adapter boundary.

    Implementations may write the derived document to
    an actual search backend.

    They must never mutate CORE-004 source truth.
    """

    def upsert(
        self,
        document: InventoryIndexDocument,
    ) -> None:
        ...

    def delete(
        self,
        document: InventoryIndexDocument,
    ) -> None:
        ...


@dataclass(slots=True)
class SearchProjectionSynchronizer:
    """
    Deterministic source-event -> search-projection boundary.

    Synchronization rule:
        newer source version may replace older projection version.

    Duplicate rule:
        same event_id is ignored.

    Out-of-order rule:
        older source versions are ignored.

    Same-version/different-event rule:
        treated as CONFLICT and fail closed.

    No source mutation occurs.
    """

    sink: SearchProjectionSink | None = None

    def __post_init__(self) -> None:
        self._versions: dict[
            tuple[str, str],
            ProjectionVersion,
        ] = {}

        self._processed_events: set[str] = set()

    def _key(
        self,
        event: SearchSourceEvent,
    ) -> tuple[str, str]:
        return (
            event.tenant_id,
            event.inventory.identity_key,
        )

    def _validate_tenant(
        self,
        event: SearchSourceEvent,
    ) -> None:
        if (
            event.tenant_id
            != event.inventory.tenant_id
        ):
            raise ProjectionTenantError(
                "Source event tenant does not match "
                "inventory tenant."
            )

    def _build_document(
        self,
        event: SearchSourceEvent,
    ) -> InventoryIndexDocument:
        if (
            event.operation
            is ProjectionOperation.UPSERT
        ):
            return build_inventory_index(
                event.inventory
            )

        if (
            event.operation
            is ProjectionOperation.DELETE
        ):
            return build_inventory_index_delete(
                event.inventory
            )

        raise ProjectionEventError(
            "Unsupported projection operation."
        )

    def consume(
        self,
        event: SearchSourceEvent,
    ) -> ProjectionChange:
        if not isinstance(
            event,
            SearchSourceEvent,
        ):
            raise ProjectionEventError(
                "event must be SearchSourceEvent."
            )

        self._validate_tenant(event)

        key = self._key(event)

        if event.event_id in self._processed_events:
            previous = self._versions.get(key)

            return ProjectionChange(
                status=ProjectionApplyStatus.DUPLICATE,
                event_id=event.event_id,
                tenant_id=event.tenant_id,
                index_key=event.inventory.identity_key,
                source_version=event.source_version,
                document=None,
                reason="Event was already consumed.",
            )

        current = self._versions.get(key)

        if current is not None:
            if event.source_version < current.source_version:
                self._processed_events.add(
                    event.event_id
                )

                return ProjectionChange(
                    status=ProjectionApplyStatus.STALE,
                    event_id=event.event_id,
                    tenant_id=event.tenant_id,
                    index_key=event.inventory.identity_key,
                    source_version=event.source_version,
                    document=None,
                    reason=(
                        "Out-of-order source event is older "
                        "than the projected version."
                    ),
                )

            if event.source_version == current.source_version:
                self._processed_events.add(
                    event.event_id
                )

                return ProjectionChange(
                    status=ProjectionApplyStatus.CONFLICT,
                    event_id=event.event_id,
                    tenant_id=event.tenant_id,
                    index_key=event.inventory.identity_key,
                    source_version=event.source_version,
                    document=None,
                    reason=(
                        "Different event attempted to produce "
                        "the same source version."
                    ),
                )

        document = self._build_document(event)

        if (
            document.inventory_version
            != event.source_version
        ):
            raise ProjectionVersionError(
                "Projection document version does not match "
                "source event version."
            )

        if self.sink is not None:
            if document.operation is SearchIndexOperation.UPSERT:
                self.sink.upsert(document)
            else:
                self.sink.delete(document)

        projection_state = ProjectionVersion(
            tenant_id=event.tenant_id,
            index_key=event.inventory.identity_key,
            source_version=event.source_version,
            projection_version=event.source_version,
            last_event_id=event.event_id,
        )

        self._versions[key] = projection_state
        self._processed_events.add(event.event_id)

        return ProjectionChange(
            status=ProjectionApplyStatus.APPLIED,
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            index_key=event.inventory.identity_key,
            source_version=event.source_version,
            document=document,
            reason="Projection applied.",
        )

    def consume_many(
        self,
        events: Iterable[SearchSourceEvent],
    ) -> tuple[ProjectionChange, ...]:
        if isinstance(events, (str, bytes)):
            raise ProjectionEventError(
                "events must be an iterable of SearchSourceEvent."
            )

        materialized = list(events)

        for event in materialized:
            if not isinstance(
                event,
                SearchSourceEvent,
            ):
                raise ProjectionEventError(
                    "events must contain SearchSourceEvent values."
                )

        # Deterministic source ordering.
        materialized.sort(
            key=lambda event: (
                event.tenant_id.casefold(),
                event.inventory.identity_key.casefold(),
                event.source_version,
                event.event_id,
            )
        )

        return tuple(
            self.consume(event)
            for event in materialized
        )

    def projection_state(
        self,
        *,
        tenant_id: str,
        index_key: str,
    ) -> ProjectionVersion | None:
        return self._versions.get(
            (
                tenant_id,
                index_key,
            )
        )

    def is_projection_stale(
        self,
        *,
        tenant_id: str,
        index_key: str,
        source_version: int,
    ) -> bool:
        if (
            isinstance(source_version, bool)
            or not isinstance(
                source_version,
                int,
            )
            or source_version < 1
        ):
            raise ProjectionVersionError(
                "source_version must be a positive integer."
            )

        state = self.projection_state(
            tenant_id=tenant_id,
            index_key=index_key,
        )

        if state is None:
            return True

        return (
            state.projection_version
            < source_version
        )

    def rebuild_documents(
        self,
        inventories: Iterable[Inventory],
    ) -> tuple[InventoryIndexDocument, ...]:
        """
        Deterministic rebuild/reindex handoff.

        Full backend rebuild execution remains delegated to
        the dedicated CORE-005 rebuild adapter/pipeline.
        """
        if isinstance(inventories, (str, bytes)):
            raise ProjectionEventError(
                "inventories must be iterable."
            )

        materialized = list(inventories)

        for inventory in materialized:
            if not isinstance(
                inventory,
                Inventory,
            ):
                raise ProjectionEventError(
                    "rebuild input must contain CORE-004 Inventory."
                )

        materialized.sort(
            key=lambda inventory: (
                inventory.tenant_id.casefold(),
                inventory.identity_key.casefold(),
                inventory.version,
            )
        )

        return tuple(
            build_inventory_index(
                inventory
            )
            for inventory in materialized
        )


__all__ = [
    "ProjectionSyncError",
    "ProjectionTenantError",
    "ProjectionVersionError",
    "ProjectionEventError",
    "ProjectionApplyStatus",
    "ProjectionOperation",
    "SearchSourceEvent",
    "ProjectionVersion",
    "ProjectionChange",
    "SearchProjectionSink",
    "SearchProjectionSynchronizer",
]
