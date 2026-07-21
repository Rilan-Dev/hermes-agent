from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass

from agentic_platform.auth.contracts import Permission, Principal
from agentic_platform.auth.service import AuthorizationService
from agentic_platform.domain.errors import DomainError, DomainValidationError
from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent
from agentic_platform.ports.repositories import UnitOfWork


PrincipalResolver = Callable[[Principal], Awaitable[Principal]]


@dataclass(frozen=True, slots=True)
class RealtimeConfig:
    batch_limit: int = 100
    poll_interval_seconds: float = 0.25
    max_buffered_events: int = 500

    def __post_init__(self) -> None:
        if not isinstance(self.batch_limit, int) or isinstance(self.batch_limit, bool):
            raise DomainValidationError("realtime batch limit must be an integer")
        if self.batch_limit <= 0:
            raise DomainValidationError("realtime batch limit must be positive")
        if not isinstance(self.max_buffered_events, int) or isinstance(
            self.max_buffered_events, bool
        ):
            raise DomainValidationError("realtime buffer limit must be an integer")
        if self.max_buffered_events <= 0:
            raise DomainValidationError("realtime buffer limit must be positive")
        if self.poll_interval_seconds <= 0:
            raise DomainValidationError("realtime poll interval must be positive")


class SlowConsumerError(DomainError):
    def __init__(self, last_delivered_cursor: EventCursor) -> None:
        self.last_delivered_cursor = last_delivered_cursor
        super().__init__("reconnect with the supplied cursor")


class RealtimeService:
    def __init__(
        self,
        *,
        unit_of_work_factory: Callable[[], UnitOfWork],
        authorization: AuthorizationService,
        principal_resolver: PrincipalResolver,
        config: RealtimeConfig | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._authorization = authorization
        self._principal_resolver = principal_resolver
        self._config = config or RealtimeConfig()

    async def read_batch(
        self,
        *,
        principal: Principal,
        workspace_id: WorkspaceId,
        after: EventCursor | None,
        limit: int | None = None,
    ) -> Sequence[WorkspaceEvent]:
        requested_limit = self._config.batch_limit if limit is None else limit
        if not isinstance(requested_limit, int) or isinstance(requested_limit, bool):
            raise DomainValidationError("realtime read limit must be an integer")
        if requested_limit <= 0:
            raise DomainValidationError("realtime read limit must be positive")
        requested_limit = min(requested_limit, self._config.batch_limit)

        current_principal = await self._principal_resolver(principal)
        self._authorization.require(
            current_principal,
            Permission.INBOX_READ,
            resource_workspace_id=workspace_id,
        )

        async with self._unit_of_work_factory() as unit_of_work:
            pending = await unit_of_work.outbox.read(
                workspace_id,
                after=after,
                limit=self._config.max_buffered_events + 1,
            )

        if len(pending) > self._config.max_buffered_events:
            raise SlowConsumerError(after or EventCursor(0))
        return tuple(pending[:requested_limit])

    async def subscribe(
        self,
        *,
        principal: Principal,
        workspace_id: WorkspaceId,
        after: EventCursor | None,
    ) -> AsyncIterator[WorkspaceEvent]:
        cursor = after or EventCursor(0)
        while True:
            batch = await self.read_batch(
                principal=principal,
                workspace_id=workspace_id,
                after=cursor,
            )
            if not batch:
                await asyncio.sleep(self._config.poll_interval_seconds)
                continue
            for event in batch:
                cursor = event.cursor
                yield event
