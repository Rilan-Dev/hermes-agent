from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from agentic_platform.domain.channels import ChannelConnection, NativeReference
from agentic_platform.domain.errors import CrossWorkspaceError
from agentic_platform.domain.events import ChannelEvent, ChannelEventKind
from agentic_platform.domain.ids import EventId, WorkspaceId
from agentic_platform.domain.inbox import Conversation, ConversationType
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent
from agentic_platform.storage.memory import MemoryDatabase, MemoryUnitOfWork


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)


def _workspace() -> Workspace:
    return Workspace.create(name="Acme Support", created_at=NOW)


def _connection(workspace_id: WorkspaceId) -> ChannelConnection:
    return ChannelConnection.create(
        workspace_id=workspace_id,
        platform_id="telegram",
        display_name="Support Bot",
        created_at=NOW,
    )


def test_memory_unit_of_work_commits_aggregate_and_outbox_atomically() -> None:
    async def scenario() -> None:
        database = MemoryDatabase()
        workspace = _workspace()
        connection = _connection(workspace.id)
        conversation = Conversation.create(
            workspace_id=workspace.id,
            connection=connection,
            native=NativeReference("telegram", "chat-1"),
            conversation_type=ConversationType.DIRECT,
            created_at=NOW,
        )
        outbox_event = WorkspaceEvent.create(
            workspace_id=workspace.id,
            cursor=EventCursor(1),
            event_id=EventId.new(),
            aggregate_type="conversation",
            aggregate_id=str(conversation.id),
            event_type="conversation.created",
            payload={"native_id": conversation.native.native_id},
            occurred_at=NOW,
        )

        async with MemoryUnitOfWork(database) as uow:
            await uow.workspaces.save(workspace.id, workspace)
            await uow.conversations.save(workspace.id, conversation)
            await uow.outbox.append(workspace.id, outbox_event)
            await uow.commit()

        async with MemoryUnitOfWork(database) as verification:
            assert await verification.workspaces.get(workspace.id) == workspace
            assert (
                await verification.conversations.get(workspace.id, conversation.id)
                == conversation
            )
            assert await verification.outbox.read(
                workspace.id,
                after=None,
                limit=10,
            ) == (outbox_event,)

    asyncio.run(scenario())


def test_memory_unit_of_work_rolls_back_all_changes_on_exception() -> None:
    async def scenario() -> None:
        database = MemoryDatabase()
        workspace = _workspace()
        event = WorkspaceEvent.create(
            workspace_id=workspace.id,
            cursor=EventCursor(1),
            event_id=EventId.new(),
            aggregate_type="workspace",
            aggregate_id=str(workspace.id),
            event_type="workspace.created",
            payload={},
            occurred_at=NOW,
        )

        with pytest.raises(RuntimeError, match="abort"):
            async with MemoryUnitOfWork(database) as uow:
                await uow.workspaces.save(workspace.id, workspace)
                await uow.outbox.append(workspace.id, event)
                raise RuntimeError("abort")

        async with MemoryUnitOfWork(database) as verification:
            assert await verification.workspaces.get(workspace.id) is None
            assert await verification.outbox.read(
                workspace.id,
                after=None,
                limit=10,
            ) == ()

    asyncio.run(scenario())


def test_memory_repositories_enforce_workspace_isolation() -> None:
    async def scenario() -> None:
        database = MemoryDatabase()
        workspace = _workspace()
        other_workspace_id = WorkspaceId.new()
        connection = _connection(workspace.id)
        conversation = Conversation.create(
            workspace_id=workspace.id,
            connection=connection,
            native=NativeReference("telegram", "chat-2"),
            conversation_type=ConversationType.DIRECT,
            created_at=NOW,
        )

        async with MemoryUnitOfWork(database) as uow:
            with pytest.raises(CrossWorkspaceError):
                await uow.conversations.save(other_workspace_id, conversation)
            await uow.conversations.save(workspace.id, conversation)
            await uow.commit()

        async with MemoryUnitOfWork(database) as verification:
            assert (
                await verification.conversations.get(other_workspace_id, conversation.id)
                is None
            )
            assert (
                await verification.conversations.get(workspace.id, conversation.id)
                == conversation
            )

    asyncio.run(scenario())


def test_duplicate_channel_event_key_preserves_original_event() -> None:
    async def scenario() -> None:
        database = MemoryDatabase()
        workspace = _workspace()
        connection = _connection(workspace.id)
        first = ChannelEvent.create(
            workspace_id=workspace.id,
            connection=connection,
            platform_event_id="update-100",
            kind=ChannelEventKind.MESSAGE,
            occurred_at=NOW,
        )
        duplicate = ChannelEvent.create(
            workspace_id=workspace.id,
            connection=connection,
            platform_event_id="update-100",
            kind=ChannelEventKind.MESSAGE_EDIT,
            occurred_at=NOW,
        )

        async with MemoryUnitOfWork(database) as uow:
            await uow.channel_events.save(workspace.id, first)
            await uow.channel_events.save(workspace.id, duplicate)
            await uow.commit()

        async with MemoryUnitOfWork(database) as verification:
            stored = await verification.channel_events.get_by_idempotency_key(
                workspace.id,
                connection.id,
                "update-100",
            )
            assert stored == first
            assert stored != duplicate

    asyncio.run(scenario())
