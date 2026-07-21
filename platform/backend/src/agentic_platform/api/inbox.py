from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict

from agentic_platform.api.dependencies import principal_from_headers
from agentic_platform.auth.contracts import Permission, Principal
from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.domain.inbox import Conversation
from agentic_platform.services.inbox import InboxService


router = APIRouter(prefix="/api/workspaces/{workspace_id}/inbox")


class ConversationItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    connection_id: str
    platform_id: str
    native_id: str
    conversation_type: str
    status: str
    unread_count: int
    last_message_text: str | None
    last_message_at: str | None

    @classmethod
    def from_domain(cls, value: Conversation) -> ConversationItem:
        return cls(
            id=str(value.id),
            connection_id=str(value.connection_id),
            platform_id=value.native.platform_id,
            native_id=value.native.native_id,
            conversation_type=value.conversation_type.value,
            status=value.status.value,
            unread_count=value.unread_count,
            last_message_text=value.last_message_text,
            last_message_at=(
                value.last_message_at.isoformat()
                if value.last_message_at is not None
                else None
            ),
        )


class ConversationPageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: tuple[ConversationItem, ...]
    next_cursor: str | None


@router.get("/conversations", response_model=ConversationPageResponse)
async def list_conversations(
    workspace_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(principal_from_headers)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    after: str | None = None,
) -> ConversationPageResponse:
    parsed_workspace_id = WorkspaceId.parse(workspace_id)
    dependencies = request.app.state.dependencies
    dependencies.authorization.require(
        principal,
        Permission.INBOX_READ,
        resource_workspace_id=parsed_workspace_id,
    )
    page = await InboxService(dependencies.unit_of_work_factory).list_conversations(
        parsed_workspace_id,
        limit=limit,
        after=after,
    )
    return ConversationPageResponse(
        items=tuple(ConversationItem.from_domain(item) for item in page.items),
        next_cursor=page.next_cursor,
    )


@router.post("/authorize-write")
async def authorize_write(
    workspace_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(principal_from_headers)],
) -> dict[str, bool]:
    dependencies = request.app.state.dependencies
    dependencies.authorization.require(
        principal,
        Permission.INBOX_WRITE,
        resource_workspace_id=WorkspaceId.parse(workspace_id),
    )
    return {"authorized": True}
