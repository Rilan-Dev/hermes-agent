from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agentic_platform.auth.contracts import Principal
from agentic_platform.auth.service import (
    AuthorizationService,
    ResourceNotFound,
)
from agentic_platform.domain.ids import EventId, UserId, WorkspaceId
from agentic_platform.domain.workspaces import MembershipRole
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent
from agentic_platform.services.realtime import (
    RealtimeConfig,
    RealtimeService,
    SlowConsumerError,
)
from agentic_platform.storage.memory import MemoryDatabase, MemoryUnitOfWork


NOW = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)


async def _identity_principal(principal: Principal) -> Principal:
    return principal


def _principal(workspace_id: WorkspaceId) -> Principal:
    return Principal(
        user_id=UserId.new(),
        workspace_id=workspace_id,
        role=MembershipRole.OPERATOR,
    )


async def _seed_events(
    database: MemoryDatabase,
    workspace_id: WorkspaceId,
    cursors: tuple[int, ...],
) -> None:
    async with MemoryUnitOfWork(database) as unit_of_work:
        for cursor in cursors:
            await unit_of_work.outbox.append(
                workspace_id,
                WorkspaceEvent.create(
                    workspace_id=workspace_id,
                    cursor=EventCursor(cursor),
                    event_id=EventId.new(),
                    aggregate_type="message",
                    aggregate_id=f"message-{cursor}",
                    event_type="message.created",
                    payload={"cursor": cursor},
                    occurred_at=NOW,
                ),
            )
        await unit_of_work.commit()


@pytest.mark.asyncio
async def test_subscribe_resumes_after_last_cursor() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    await _seed_events(database, workspace_id, (1, 2, 3))
    service = RealtimeService(
        unit_of_work_factory=lambda: MemoryUnitOfWork(database),
        authorization=AuthorizationService(),
        principal_resolver=_identity_principal,
        config=RealtimeConfig(batch_limit=2, poll_interval_seconds=0.001),
    )

    stream = service.subscribe(
        principal=_principal(workspace_id),
        workspace_id=workspace_id,
        after=EventCursor(1),
    )

    assert (await anext(stream)).cursor == EventCursor(2)
    assert (await anext(stream)).cursor == EventCursor(3)
    await stream.aclose()


@pytest.mark.asyncio
async def test_read_batch_rejects_backlog_larger_than_buffer() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    await _seed_events(database, workspace_id, (1, 2))
    service = RealtimeService(
        unit_of_work_factory=lambda: MemoryUnitOfWork(database),
        authorization=AuthorizationService(),
        principal_resolver=_identity_principal,
        config=RealtimeConfig(max_buffered_events=1),
    )

    with pytest.raises(SlowConsumerError) as exc_info:
        await service.read_batch(
            principal=_principal(workspace_id),
            workspace_id=workspace_id,
            after=None,
        )

    assert exc_info.value.last_delivered_cursor == EventCursor(0)


@pytest.mark.asyncio
async def test_subscribe_rechecks_principal_before_each_batch() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    await _seed_events(database, workspace_id, (1, 2))
    calls = 0

    async def resolver(principal: Principal) -> Principal:
        nonlocal calls
        calls += 1
        if calls == 1:
            return principal
        raise ResourceNotFound("resource was not found")

    service = RealtimeService(
        unit_of_work_factory=lambda: MemoryUnitOfWork(database),
        authorization=AuthorizationService(),
        principal_resolver=resolver,
        config=RealtimeConfig(batch_limit=1, poll_interval_seconds=0.001),
    )
    stream = service.subscribe(
        principal=_principal(workspace_id),
        workspace_id=workspace_id,
        after=None,
    )

    assert (await anext(stream)).cursor == EventCursor(1)
    with pytest.raises(ResourceNotFound):
        await anext(stream)
    await stream.aclose()
    assert calls == 2
