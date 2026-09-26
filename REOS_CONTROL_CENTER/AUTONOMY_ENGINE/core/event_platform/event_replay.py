from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Iterable
from uuid import UUID, uuid4

from .event_domain import EventEnvelope


class ReplayError(ValueError):
    """Base replay error."""


class ReplayAuthorizationError(
    ReplayError
):
    """Raised when replay is not authorized."""


class ReplayScopeError(ReplayError):
    """Raised when replay scope is invalid."""


class ReplayDuplicateError(ReplayError):
    """Raised when replay identity was already processed."""


class ReplayStatus(str, Enum):
    REQUESTED = "REQUESTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ReplayScope:
    tenant_id: UUID
    event_ids: tuple[UUID, ...]
    requested_by: UUID

    def __post_init__(self) -> None:
        if not isinstance(
            self.tenant_id,
            UUID,
        ):
            raise TypeError(
                "tenant_id must be UUID"
            )

        if not isinstance(
            self.requested_by,
            UUID,
        ):
            raise TypeError(
                "requested_by must be UUID"
            )

        if not self.event_ids:
            raise ReplayScopeError(
                "replay scope cannot be empty"
            )

        if len(self.event_ids) != len(
            set(self.event_ids)
        ):
            raise ReplayScopeError(
                "replay scope contains duplicate event ids"
            )


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    replay_id: UUID
    scope: ReplayScope
    requested_at: datetime


@dataclass(frozen=True, slots=True)
class ReplayResult:
    replay_id: UUID
    status: ReplayStatus
    processed_event_ids: tuple[UUID, ...]
    failed_event_ids: tuple[UUID, ...]


class ReplayAuthorizationBoundary:
    """
    Authorization boundary.

    Actual identity/authorization authority remains outside
    CORE-002.
    """

    def __init__(
        self,
        checker: Callable[
            [UUID, UUID],
            bool,
        ],
    ) -> None:
        self._checker = checker

    def authorize(
        self,
        *,
        tenant_id: UUID,
        requester_id: UUID,
    ) -> None:
        if not self._checker(
            tenant_id,
            requester_id,
        ):
            raise ReplayAuthorizationError(
                "replay requester is not authorized"
            )


class ReplayCoordinator:
    """
    Deterministic replay coordinator.

    Responsibilities:
    - validate replay scope
    - enforce tenant boundary
    - establish replay identity
    - process events in supplied deterministic order
    - report partial failures

    Not responsible for:
    - persistent replay storage
    - transport
    - Control Center state
    - authorization engine
    - idempotency engine
    """

    def __init__(
        self,
        *,
        authorization: ReplayAuthorizationBoundary,
        duplicate_checker: Callable[[UUID], bool],
        mark_replay: Callable[[UUID], None],
    ) -> None:
        self._authorization = authorization
        self._duplicate_checker = duplicate_checker
        self._mark_replay = mark_replay

    def create_request(
        self,
        *,
        scope: ReplayScope,
    ) -> ReplayRequest:
        self._authorization.authorize(
            tenant_id=scope.tenant_id,
            requester_id=scope.requested_by,
        )

        replay_id = uuid4()

        if self._duplicate_checker(
            replay_id
        ):
            raise ReplayDuplicateError(
                "generated replay identity already exists"
            )

        self._mark_replay(replay_id)

        return ReplayRequest(
            replay_id=replay_id,
            scope=scope,
            requested_at=datetime.now(timezone.utc),
        )

    def execute(
        self,
        *,
        request: ReplayRequest,
        events: Iterable[EventEnvelope],
        handler: Callable[
            [EventEnvelope],
            None,
        ],
    ) -> ReplayResult:
        if not callable(handler):
            raise TypeError(
                "handler must be callable"
            )

        allowed_ids = set(
            request.scope.event_ids
        )

        selected: list[EventEnvelope] = []

        for event in events:
            if event.event_id not in allowed_ids:
                continue

            if event.tenant_id != (
                request.scope.tenant_id
            ):
                raise ReplayScopeError(
                    "cross-tenant event encountered "
                    "during replay"
                )

            selected.append(event)

        selected.sort(
            key=lambda item: (
                item.sequence
                if item.sequence is not None
                else -1,
                str(item.event_id),
            )
        )

        processed: list[UUID] = []
        failed: list[UUID] = []

        for event in selected:
            try:
                handler(event)
                processed.append(
                    event.event_id
                )
            except Exception:
                failed.append(
                    event.event_id
                )

        if failed and processed:
            status = ReplayStatus.PARTIAL_FAILURE
        elif failed:
            status = ReplayStatus.FAILED
        else:
            status = ReplayStatus.COMPLETED

        return ReplayResult(
            replay_id=request.replay_id,
            status=status,
            processed_event_ids=tuple(
                processed
            ),
            failed_event_ids=tuple(
                failed
            ),
        )


__all__ = [
    "ReplayError",
    "ReplayAuthorizationError",
    "ReplayScopeError",
    "ReplayDuplicateError",
    "ReplayStatus",
    "ReplayScope",
    "ReplayRequest",
    "ReplayResult",
    "ReplayAuthorizationBoundary",
    "ReplayCoordinator",
]
