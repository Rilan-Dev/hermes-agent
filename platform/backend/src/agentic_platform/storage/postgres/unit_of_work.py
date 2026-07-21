from __future__ import annotations

from types import TracebackType
from typing import TypeVar

from agentic_platform.storage.postgres.protocols import (
    PostgresConnection,
    PostgresPool,
    PostgresTransaction,
)
from agentic_platform.storage.postgres.repositories import (
    PostgresChannelEventRepository,
    PostgresContactRepository,
    PostgresConversationRepository,
    PostgresExternalIdentityRepository,
    PostgresMessageRepository,
    PostgresOutboxRepository,
    PostgresWorkspaceRepository,
)


_RepositoryT = TypeVar("_RepositoryT")


class PostgresUnitOfWork:
    def __init__(self, pool: PostgresPool) -> None:
        self._pool = pool
        self._connection: PostgresConnection | None = None
        self._transaction: PostgresTransaction | None = None
        self._commit_requested = False
        self._entered = False
        self._workspaces: PostgresWorkspaceRepository | None = None
        self._contacts: PostgresContactRepository | None = None
        self._external_identities: PostgresExternalIdentityRepository | None = None
        self._conversations: PostgresConversationRepository | None = None
        self._messages: PostgresMessageRepository | None = None
        self._channel_events: PostgresChannelEventRepository | None = None
        self._outbox: PostgresOutboxRepository | None = None

    async def __aenter__(self) -> PostgresUnitOfWork:
        if self._entered:
            raise RuntimeError("postgres unit of work cannot be re-entered")
        connection = await self._pool.acquire()
        transaction = connection.transaction()
        try:
            await transaction.start()
        except BaseException:
            await self._pool.release(connection)
            raise
        self._entered = True
        self._connection = connection
        self._transaction = transaction
        self._workspaces = PostgresWorkspaceRepository(connection)
        self._contacts = PostgresContactRepository(connection)
        self._external_identities = PostgresExternalIdentityRepository(connection)
        self._conversations = PostgresConversationRepository(connection)
        self._messages = PostgresMessageRepository(connection)
        self._channel_events = PostgresChannelEventRepository(connection)
        self._outbox = PostgresOutboxRepository(connection)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        del exc, traceback
        self._require_entered()
        assert self._connection is not None
        assert self._transaction is not None
        try:
            if exc_type is None and self._commit_requested:
                await self._transaction.commit()
            else:
                await self._transaction.rollback()
        finally:
            connection = self._connection
            self._reset()
            await self._pool.release(connection)
        return None

    @property
    def workspaces(self) -> PostgresWorkspaceRepository:
        return self._require_repository(self._workspaces)

    @property
    def contacts(self) -> PostgresContactRepository:
        return self._require_repository(self._contacts)

    @property
    def external_identities(self) -> PostgresExternalIdentityRepository:
        return self._require_repository(self._external_identities)

    @property
    def conversations(self) -> PostgresConversationRepository:
        return self._require_repository(self._conversations)

    @property
    def messages(self) -> PostgresMessageRepository:
        return self._require_repository(self._messages)

    @property
    def channel_events(self) -> PostgresChannelEventRepository:
        return self._require_repository(self._channel_events)

    @property
    def outbox(self) -> PostgresOutboxRepository:
        return self._require_repository(self._outbox)

    async def commit(self) -> None:
        self._require_entered()
        self._commit_requested = True

    async def rollback(self) -> None:
        self._require_entered()
        self._commit_requested = False

    def _require_entered(self) -> None:
        if not self._entered:
            raise RuntimeError("postgres unit of work must be entered before use")

    def _require_repository(
        self,
        repository: _RepositoryT | None,
    ) -> _RepositoryT:
        self._require_entered()
        assert repository is not None
        return repository

    def _reset(self) -> None:
        self._entered = False
        self._commit_requested = False
        self._connection = None
        self._transaction = None
        self._workspaces = None
        self._contacts = None
        self._external_identities = None
        self._conversations = None
        self._messages = None
        self._channel_events = None
        self._outbox = None
