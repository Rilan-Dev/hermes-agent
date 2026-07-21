from __future__ import annotations

from types import TracebackType
from typing import Protocol, Sequence

from agentic_platform.domain.channels import Contact, ExternalIdentity
from agentic_platform.domain.events import ChannelEvent
from agentic_platform.domain.ids import (
    ConnectionId,
    ContactId,
    ConversationId,
    MessageId,
    WorkspaceId,
)
from agentic_platform.domain.inbox import Conversation, Message
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent


class WorkspaceRepository(Protocol):
    async def get(self, workspace_id: WorkspaceId) -> Workspace | None: ...

    async def save(
        self,
        workspace_id: WorkspaceId,
        workspace: Workspace,
    ) -> None: ...


class ContactRepository(Protocol):
    async def get(
        self,
        workspace_id: WorkspaceId,
        contact_id: ContactId,
    ) -> Contact | None: ...

    async def save(
        self,
        workspace_id: WorkspaceId,
        contact: Contact,
    ) -> None: ...


class ExternalIdentityRepository(Protocol):
    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        native_id: str,
    ) -> ExternalIdentity | None: ...

    async def save(
        self,
        workspace_id: WorkspaceId,
        identity: ExternalIdentity,
    ) -> None: ...


class ConversationRepository(Protocol):
    async def get(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
    ) -> Conversation | None: ...

    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        native_id: str,
    ) -> Conversation | None: ...

    async def list_recent(
        self,
        workspace_id: WorkspaceId,
        *,
        limit: int,
        after: str | None = None,
    ) -> Sequence[Conversation]: ...

    async def save(
        self,
        workspace_id: WorkspaceId,
        conversation: Conversation,
    ) -> None: ...


class MessageRepository(Protocol):
    async def get(
        self,
        workspace_id: WorkspaceId,
        message_id: MessageId,
    ) -> Message | None: ...

    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        native_id: str,
    ) -> Message | None: ...

    async def list_for_conversation(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        *,
        limit: int,
        after: str | None = None,
    ) -> Sequence[Message]: ...

    async def save(
        self,
        workspace_id: WorkspaceId,
        message: Message,
    ) -> None: ...


class ChannelEventRepository(Protocol):
    async def get_by_idempotency_key(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        platform_event_id: str,
    ) -> ChannelEvent | None: ...

    async def save(
        self,
        workspace_id: WorkspaceId,
        event: ChannelEvent,
    ) -> None: ...


class OutboxRepository(Protocol):
    async def next_cursor(self, workspace_id: WorkspaceId) -> EventCursor: ...

    async def append(
        self,
        workspace_id: WorkspaceId,
        event: WorkspaceEvent,
    ) -> None: ...

    async def read(
        self,
        workspace_id: WorkspaceId,
        *,
        after: EventCursor | None,
        limit: int,
    ) -> Sequence[WorkspaceEvent]: ...


class UnitOfWork(Protocol):
    @property
    def workspaces(self) -> WorkspaceRepository: ...

    @property
    def contacts(self) -> ContactRepository: ...

    @property
    def external_identities(self) -> ExternalIdentityRepository: ...

    @property
    def conversations(self) -> ConversationRepository: ...

    @property
    def messages(self) -> MessageRepository: ...

    @property
    def channel_events(self) -> ChannelEventRepository: ...

    @property
    def outbox(self) -> OutboxRepository: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
