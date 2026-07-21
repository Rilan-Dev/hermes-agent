from __future__ import annotations

import json
from collections.abc import Sequence

from agentic_platform.domain.channels import Contact, ExternalIdentity
from agentic_platform.domain.errors import CrossWorkspaceError, DomainValidationError
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
from agentic_platform.storage.postgres.codec import (
    channel_event_from_row,
    contact_from_row,
    conversation_from_row,
    external_identity_from_row,
    message_from_row,
    workspace_event_from_row,
    workspace_from_row,
)
from agentic_platform.storage.postgres.protocols import RepositoryConnection


_CONVERSATION_SELECT = """
SELECT workspace_id, id, connection_id, platform_id, native_id,
       conversation_type, status, created_at, updated_at, unread_count,
       last_message_text, last_message_at
FROM conversations
""".strip()
_CONVERSATION_GET_SQL = (
    _CONVERSATION_SELECT + " WHERE workspace_id = $1 AND id = $2"
)
_CONVERSATION_GET_NATIVE_SQL = (
    _CONVERSATION_SELECT
    + " WHERE workspace_id = $1 AND connection_id = $2 AND native_id = $3"
)
_CONVERSATION_LIST_SQL = (
    _CONVERSATION_SELECT
    + """
 WHERE workspace_id = $1
  AND (
      $3::uuid IS NULL
      OR (updated_at, id) < (
          SELECT updated_at, id
          FROM conversations
          WHERE workspace_id = $1 AND id = $3
      )
  )
ORDER BY updated_at DESC, id DESC
LIMIT $2
"""
).strip()

_MESSAGE_SELECT = """
SELECT workspace_id, id, conversation_id, platform_id, native_id, direction,
       text, sent_at, delivery_state, reply_to_native_id, thread_native_id
FROM messages
""".strip()
_MESSAGE_GET_SQL = _MESSAGE_SELECT + " WHERE workspace_id = $1 AND id = $2"
_MESSAGE_GET_NATIVE_SQL = (
    _MESSAGE_SELECT
    + " WHERE workspace_id = $1 AND conversation_id = $2 AND native_id = $3"
)
_MESSAGE_LIST_SQL = (
    _MESSAGE_SELECT
    + """
 WHERE workspace_id = $1
  AND conversation_id = $2
  AND (
      $4::uuid IS NULL
      OR (sent_at, id) > (
          SELECT sent_at, id
          FROM messages
          WHERE workspace_id = $1 AND conversation_id = $2 AND id = $4
      )
  )
ORDER BY sent_at ASC, id ASC
LIMIT $3
"""
).strip()

_CHANNEL_EVENT_GET_SQL = """
SELECT workspace_id, id, connection_id, platform_event_id, kind, occurred_at,
       native_target_platform_id, native_target_id, raw_payload_ref
FROM channel_events
WHERE workspace_id = $1 AND connection_id = $2 AND platform_event_id = $3
""".strip()


def _require_workspace(
    requested: WorkspaceId,
    actual: WorkspaceId,
    *,
    aggregate: str,
) -> None:
    if requested != actual:
        raise CrossWorkspaceError(
            f"{aggregate} repository cannot cross workspace boundaries"
        )


def _validate_limit(limit: int) -> None:
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise DomainValidationError("repository limit must be a positive integer")


class _Repository:
    def __init__(self, connection: RepositoryConnection) -> None:
        self._connection = connection


class PostgresWorkspaceRepository(_Repository):
    async def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        row = await self._connection.fetchrow(
            "SELECT id, name, created_at FROM workspaces WHERE id = $1",
            workspace_id.value,
        )
        return workspace_from_row(row) if row is not None else None

    async def save(
        self,
        workspace_id: WorkspaceId,
        workspace: Workspace,
    ) -> None:
        _require_workspace(workspace_id, workspace.id, aggregate="workspace")
        await self._connection.execute(
            """
INSERT INTO workspaces(id, name, created_at)
VALUES ($1, $2, $3)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
""".strip(),
            workspace.id.value,
            workspace.name,
            workspace.created_at,
        )


class PostgresContactRepository(_Repository):
    async def get(
        self,
        workspace_id: WorkspaceId,
        contact_id: ContactId,
    ) -> Contact | None:
        row = await self._connection.fetchrow(
            """
SELECT workspace_id, id, display_name, created_at
FROM contacts
WHERE workspace_id = $1 AND id = $2
""".strip(),
            workspace_id.value,
            contact_id.value,
        )
        return contact_from_row(row) if row is not None else None

    async def save(self, workspace_id: WorkspaceId, contact: Contact) -> None:
        _require_workspace(workspace_id, contact.workspace_id, aggregate="contact")
        await self._connection.execute(
            """
INSERT INTO contacts(workspace_id, id, display_name, created_at)
VALUES ($1, $2, $3, $4)
ON CONFLICT (workspace_id, id) DO UPDATE
SET display_name = EXCLUDED.display_name
""".strip(),
            workspace_id.value,
            contact.id.value,
            contact.display_name,
            contact.created_at,
        )


class PostgresExternalIdentityRepository(_Repository):
    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        native_id: str,
    ) -> ExternalIdentity | None:
        row = await self._connection.fetchrow(
            """
SELECT workspace_id, id, connection_id, contact_id, platform_id, native_id,
       display_name, created_at
FROM external_identities
WHERE workspace_id = $1 AND connection_id = $2 AND native_id = $3
""".strip(),
            workspace_id.value,
            connection_id.value,
            native_id,
        )
        return external_identity_from_row(row) if row is not None else None

    async def save(
        self,
        workspace_id: WorkspaceId,
        identity: ExternalIdentity,
    ) -> None:
        _require_workspace(
            workspace_id,
            identity.workspace_id,
            aggregate="external identity",
        )
        await self._connection.execute(
            """
INSERT INTO external_identities(
    workspace_id, id, connection_id, contact_id, platform_id, native_id,
    display_name, created_at
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (workspace_id, connection_id, native_id) DO UPDATE
SET contact_id = EXCLUDED.contact_id,
    display_name = EXCLUDED.display_name
""".strip(),
            workspace_id.value,
            identity.id.value,
            identity.connection_id.value,
            identity.contact_id.value,
            identity.native.platform_id,
            identity.native.native_id,
            identity.display_name,
            identity.created_at,
        )


class PostgresConversationRepository(_Repository):
    async def get(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
    ) -> Conversation | None:
        row = await self._connection.fetchrow(
            _CONVERSATION_GET_SQL,
            workspace_id.value,
            conversation_id.value,
        )
        return conversation_from_row(row) if row is not None else None

    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        native_id: str,
    ) -> Conversation | None:
        row = await self._connection.fetchrow(
            _CONVERSATION_GET_NATIVE_SQL,
            workspace_id.value,
            connection_id.value,
            native_id,
        )
        return conversation_from_row(row) if row is not None else None

    async def list_recent(
        self,
        workspace_id: WorkspaceId,
        *,
        limit: int,
        after: str | None = None,
    ) -> Sequence[Conversation]:
        _validate_limit(limit)
        after_id = ConversationId.parse(after).value if after is not None else None
        rows = await self._connection.fetch(
            _CONVERSATION_LIST_SQL,
            workspace_id.value,
            limit,
            after_id,
        )
        return tuple(conversation_from_row(row) for row in rows)

    async def save(
        self,
        workspace_id: WorkspaceId,
        conversation: Conversation,
    ) -> None:
        _require_workspace(
            workspace_id,
            conversation.workspace_id,
            aggregate="conversation",
        )
        await self._connection.execute(
            """
INSERT INTO conversations(
    workspace_id, id, connection_id, platform_id, native_id, conversation_type,
    status, created_at, updated_at, unread_count, last_message_text, last_message_at
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
ON CONFLICT (workspace_id, id) DO UPDATE
SET status = EXCLUDED.status,
    updated_at = EXCLUDED.updated_at,
    unread_count = EXCLUDED.unread_count,
    last_message_text = EXCLUDED.last_message_text,
    last_message_at = EXCLUDED.last_message_at
""".strip(),
            workspace_id.value,
            conversation.id.value,
            conversation.connection_id.value,
            conversation.native.platform_id,
            conversation.native.native_id,
            conversation.conversation_type.value,
            conversation.status.value,
            conversation.created_at,
            conversation.updated_at,
            conversation.unread_count,
            conversation.last_message_text,
            conversation.last_message_at,
        )


class PostgresMessageRepository(_Repository):
    async def get(
        self,
        workspace_id: WorkspaceId,
        message_id: MessageId,
    ) -> Message | None:
        row = await self._connection.fetchrow(
            _MESSAGE_GET_SQL,
            workspace_id.value,
            message_id.value,
        )
        return message_from_row(row) if row is not None else None

    async def get_by_native_id(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        native_id: str,
    ) -> Message | None:
        row = await self._connection.fetchrow(
            _MESSAGE_GET_NATIVE_SQL,
            workspace_id.value,
            conversation_id.value,
            native_id,
        )
        return message_from_row(row) if row is not None else None

    async def list_for_conversation(
        self,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        *,
        limit: int,
        after: str | None = None,
    ) -> Sequence[Message]:
        _validate_limit(limit)
        after_id = MessageId.parse(after).value if after is not None else None
        rows = await self._connection.fetch(
            _MESSAGE_LIST_SQL,
            workspace_id.value,
            conversation_id.value,
            limit,
            after_id,
        )
        return tuple(message_from_row(row) for row in rows)

    async def save(self, workspace_id: WorkspaceId, message: Message) -> None:
        _require_workspace(workspace_id, message.workspace_id, aggregate="message")
        await self._connection.execute(
            """
INSERT INTO messages(
    workspace_id, id, conversation_id, platform_id, native_id, direction, text,
    sent_at, delivery_state, reply_to_native_id, thread_native_id
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
ON CONFLICT (workspace_id, id) DO UPDATE
SET text = EXCLUDED.text,
    delivery_state = EXCLUDED.delivery_state,
    reply_to_native_id = EXCLUDED.reply_to_native_id,
    thread_native_id = EXCLUDED.thread_native_id
""".strip(),
            workspace_id.value,
            message.id.value,
            message.conversation_id.value,
            message.native.platform_id,
            message.native.native_id,
            message.direction.value,
            message.text,
            message.sent_at,
            message.delivery_state.value,
            message.reply_to_native_id,
            message.thread_native_id,
        )


class PostgresChannelEventRepository(_Repository):
    async def get_by_idempotency_key(
        self,
        workspace_id: WorkspaceId,
        connection_id: ConnectionId,
        platform_event_id: str,
    ) -> ChannelEvent | None:
        lock_key = f"{workspace_id}:{connection_id}:{platform_event_id}"
        await self._connection.fetchval(
            "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
            lock_key,
        )
        row = await self._connection.fetchrow(
            _CHANNEL_EVENT_GET_SQL,
            workspace_id.value,
            connection_id.value,
            platform_event_id,
        )
        return channel_event_from_row(row) if row is not None else None

    async def save(self, workspace_id: WorkspaceId, event: ChannelEvent) -> None:
        _require_workspace(
            workspace_id,
            event.workspace_id,
            aggregate="channel event",
        )
        target_platform = (
            event.native_target.platform_id if event.native_target is not None else None
        )
        target_id = (
            event.native_target.native_id if event.native_target is not None else None
        )
        await self._connection.execute(
            """
INSERT INTO channel_events(
    workspace_id, id, connection_id, platform_event_id, kind, occurred_at,
    native_target_platform_id, native_target_id, raw_payload_ref
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
ON CONFLICT (workspace_id, connection_id, platform_event_id) DO NOTHING
""".strip(),
            workspace_id.value,
            event.id.value,
            event.connection_id.value,
            event.platform_event_id,
            event.kind.value,
            event.occurred_at,
            target_platform,
            target_id,
            event.raw_payload_ref,
        )


class PostgresOutboxRepository(_Repository):
    async def next_cursor(self, workspace_id: WorkspaceId) -> EventCursor:
        locked_workspace = await self._connection.fetchval(
            "SELECT id FROM workspaces WHERE id = $1 FOR UPDATE",
            workspace_id.value,
        )
        if locked_workspace is None:
            raise DomainValidationError("workspace does not exist")
        value = await self._connection.fetchval(
            """
SELECT COALESCE(MAX(cursor), 0) + 1
FROM workspace_outbox
WHERE workspace_id = $1
""".strip(),
            workspace_id.value,
        )
        return EventCursor.parse(value)

    async def append(self, workspace_id: WorkspaceId, event: WorkspaceEvent) -> None:
        _require_workspace(workspace_id, event.workspace_id, aggregate="outbox event")
        payload_json = json.dumps(
            dict(event.payload),
            separators=(",", ":"),
            sort_keys=True,
        )
        await self._connection.execute(
            """
INSERT INTO workspace_outbox(
    workspace_id, cursor, event_id, aggregate_type, aggregate_id, event_type,
    payload, payload_version, occurred_at
)
VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, 1, $8)
""".strip(),
            workspace_id.value,
            event.cursor.value,
            event.event_id.value,
            event.aggregate_type,
            event.aggregate_id,
            event.event_type,
            payload_json,
            event.occurred_at,
        )

    async def read(
        self,
        workspace_id: WorkspaceId,
        *,
        after: EventCursor | None,
        limit: int,
    ) -> Sequence[WorkspaceEvent]:
        _validate_limit(limit)
        cursor = after or EventCursor(0)
        rows = await self._connection.fetch(
            """
SELECT workspace_id, cursor, event_id, aggregate_type, aggregate_id,
       event_type, payload, occurred_at
FROM workspace_outbox
WHERE workspace_id = $1 AND cursor > $2
ORDER BY cursor ASC
LIMIT $3
""".strip(),
            workspace_id.value,
            cursor.value,
            limit,
        )
        return tuple(workspace_event_from_row(row) for row in rows)
