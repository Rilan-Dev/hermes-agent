from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.domain.inbox import Conversation
from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.ports.repositories import UnitOfWork


@dataclass(frozen=True, slots=True)
class ConversationPage:
    items: tuple[Conversation, ...]
    next_cursor: str | None


class InboxService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def list_conversations(
        self,
        workspace_id: WorkspaceId,
        *,
        limit: int,
        after: str | None,
    ) -> ConversationPage:
        if limit <= 0 or limit > 100:
            raise DomainValidationError("inbox limit must be between 1 and 100")
        async with self._unit_of_work_factory() as uow:
            values = tuple(
                await uow.conversations.list_recent(
                    workspace_id,
                    limit=limit + 1,
                    after=after,
                )
            )
        has_more = len(values) > limit
        items = values[:limit]
        next_cursor = str(items[-1].id) if has_more and items else None
        return ConversationPage(items=items, next_cursor=next_cursor)
