from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import TracebackType
from typing import Sequence

from agentic_platform.domain.errors import CrossWorkspaceError, DomainValidationError
from agentic_platform.domain.events import ChannelEvent
from agentic_platform.domain.ids import (
    ConnectionId,
    ConversationId,
    MessageId,
    WorkspaceId,
)
from agentic_platform.domain.inbox import Conversation, Message
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent


@dataclass(slots=True)
class _MemoryState:
    workspaces: dict[WorkspaceId, Workspace] = field(default_factory=dict)
    conversations: dict[tuple[WorkspaceId, ConversationId], Conversation] = field(
        default_factory=dict
    )
    conversation_native: dict[tuple[WorkspaceId, ConnectionId, str], ConversationId] = (
        field(default_factory=dict)
    )
    messages: dict[tuple[WorkspaceId, MessageId], Message] = field(default_factory=dict)
    message_native: dict[tuple[WorkspaceId, ConversationId, str], MessageId] = field(
        default_factory=dict
    )
    channel_events: dict[tuple[WorkspaceId, ConnectionId, str], ChannelEvent] = field(
        default_factory=dict
    )
    outbox: dict[WorkspaceId, list[WorkspaceEvent]] = field(default_factory=dict)

    def clone(self) -> _MemoryState:
        return _MemoryState(
            workspaces=dict(self.workspaces),
            conversations=dict(self.conversations),
            conversation_native=dict(self.conversation_native),
            messages=dict(self.messages),
            message_native=dict(self.message_native),
            channel_events=dict(self.channel_events),
            outbox={workspace_id: list(events) for workspace_id, events in self.outbox.items()},
        )


class MemoryDatabase:
    """Shared in-memory state used by deterministic test adapters."""

    def __init__(self) -> None:
        self._state = _MemoryState()
        self._lock = asyncio.Lock()


class _WorkspaceRepository:
    def __init__(self, state: _MemoryState) -> None:
        self._state = state

    async def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        return self._state.workspaces.get(workspace_id)

    async def save(self, workspace_id: WorkspaceId, workspace: Workspace) -> None:
        if workspace_id != workspace.id:
            raise CrossWorkspaceError("workspace repository key must match workspace ID")
        self._state.workspaces[workspace_id] = workspace


class _ConversationRepository:
    def __init__(self, state: _MemoryState) -> None:
        self._state = state

    async def get(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
    ) -> Conversation | None:
        return self._state.conversations.get((workspace_id, conversation_id))

    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        native_id: str,
    ) -> Conversation | None:
        conversation_id = self._state.conversation_native.get(
            (workspace_id, connection_id, native_id)
        )
        if conversation_id is None:
            return None
        return self._state.conversations.get((workspace_id, conversation_id))

    async def list_recent(
        self,
        workspace_id: WorkspaceId,
        *,
        limit: int,
        after: str | None = None,
    ) -> Sequence[Conversation]:
        del after
        _validate_limit(limit)
        values = [
            conversation
            for (stored_workspace_id, _), conversation in self._state.conversations.items()
            if stored_workspace_id == workspace_id
        ]
        values.sort(key=lambda item: (item.updated_at, str(item.id)), reverse=True)
        return tuple(values[:limit])

    async def save(
        self,
        workspace_id: WorkspaceId,
        conversation: Conversation,
    ) -> None:
        if workspace_id != conversation.workspace_id:
            raise CrossWorkspaceError(
                "conversation repository cannot cross workspace boundaries"
            )
        key = (workspace_id, conversation.id)
        native_key = (
            workspace_id,
            conversation.connection_id,
            conversation.native.native_id,
        )
        self._state.conversations[key] = conversation
        self._state.conversation_native[native_key] = conversation.id


class _MessageRepository:
    def __init__(self, state: _MemoryState) -> None:
        self._state = state

    async def get(
        self,
        workspace_id: WorkspaceId,
        message_id: MessageId,
    ) -> Message | None:
        return self._state.messages.get((workspace_id, message_id))

    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        native_id: str,
    ) -> Message | None:
        message_id = self._state.message_native.get(
            (workspace_id, conversation_id, native_id)
        )
        if message_id is None:
            return None
        return self._state.messages.get((workspace_id, message_id))

    async def list_for_conversation(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        *,
        limit: int,
        after: str | None = None,
    ) -> Sequence[Message]:
        del after
        _validate_limit(limit)
        values = [
            message
            for (stored_workspace_id, _), message in self._state.messages.items()
            if stored_workspace_id == workspace_id
            and message.conversation_id == conversation_id
        ]
        values.sort(key=lambda item: (item.sent_at, str(item.id)))
        return tuple(values[:limit])

    async def save(self, workspace_id: WorkspaceId, message: Message) -> None:
        if workspace_id != message.workspace_id:
            raise CrossWorkspaceError("message repository cannot cross workspace boundaries")
        key = (workspace_id, message.id)
        native_key = (workspace_id, message.conversation_id, message.native.native_id)
        self._state.messages[key] = message
        self._state.message_native[native_key] = message.id


class _ChannelEventRepository:
    def __init__(self, state: _MemoryState) -> None:
        self._state = state

    async def get_by_idempotency_key(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        platform_event_id: str,
    ) -> ChannelEvent | None:
        return self._state.channel_events.get(
            (workspace_id, connection_id, platform_event_id)
        )

    async def save(self, workspace_id: WorkspaceId, event: ChannelEvent) -> None:
        if workspace_id != event.workspace_id:
            raise CrossWorkspaceError(
                "channel-event repository cannot cross workspace boundaries"
            )
        self._state.channel_events.setdefault(event.idempotency_key, event)


class _OutboxRepository:
    def __init__(self, state: _MemoryState) -> None:
        self._state = state

    async def append(self, workspace_id: WorkspaceId, event: WorkspaceEvent) -> None:
        if workspace_id != event.workspace_id:
            raise CrossWorkspaceError("outbox event must match the requested workspace")
        events = self._state.outbox.setdefault(workspace_id, [])
        if events and event.cursor <= events[-1].cursor:
            raise DomainValidationError("outbox cursor must increase monotonically")
        events.append(event)

    async def read(
        self,
        workspace_id: WorkspaceId,
        *,
        after: EventCursor | None,
        limit: int,
    ) -> Sequence[WorkspaceEvent]:
        _validate_limit(limit)
        cursor = after or EventCursor(0)
        return tuple(
            event
            for event in self._state.outbox.get(workspace_id, [])
            if event.cursor > cursor
        )[:limit]


def _validate_limit(limit: int) -> None:
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise DomainValidationError("repository limit must be a positive integer")


class MemoryUnitOfWork:
    """Lock-protected copy-on-write unit of work for tests and prototypes."""

    def __init__(self, database: MemoryDatabase) -> None:
        self._database = database
        self._state: _MemoryState | None = None
        self._commit_requested = False
        self._entered = False
        self._workspaces: _WorkspaceRepository | None = None
        self._conversations: _ConversationRepository | None = None
        self._messages: _MessageRepository | None = None
        self._channel_events: _ChannelEventRepository | None = None
        self._outbox: _OutboxRepository | None = None

    async def __aenter__(self) -> MemoryUnitOfWork:
        if self._entered:
            raise RuntimeError("memory unit of work cannot be re-entered")
        await self._database._lock.acquire()
        self._entered = True
        self._state = self._database._state.clone()
        self._workspaces = _WorkspaceRepository(self._state)
        self._conversations = _ConversationRepository(self._state)
        self._messages = _MessageRepository(self._state)
        self._channel_events = _ChannelEventRepository(self._state)
        self._outbox = _OutboxRepository(self._state)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        del exc, traceback
        try:
            if exc_type is None and self._commit_requested:
                assert self._state is not None
                self._database._state = self._state
        finally:
            self._entered = False
            self._state = None
            self._database._lock.release()
        return None

    @property
    def workspaces(self) -> _WorkspaceRepository:
        return self._require_repository(self._workspaces)

    @property
    def conversations(self) -> _ConversationRepository:
        return self._require_repository(self._conversations)

    @property
    def messages(self) -> _MessageRepository:
        return self._require_repository(self._messages)

    @property
    def channel_events(self) -> _ChannelEventRepository:
        return self._require_repository(self._channel_events)

    @property
    def outbox(self) -> _OutboxRepository:
        return self._require_repository(self._outbox)

    async def commit(self) -> None:
        self._require_entered()
        self._commit_requested = True

    async def rollback(self) -> None:
        self._require_entered()
        self._commit_requested = False

    def _require_entered(self) -> None:
        if not self._entered:
            raise RuntimeError("memory unit of work must be entered before use")

    def _require_repository(self, repository):
        self._require_entered()
        assert repository is not None
        return repository
