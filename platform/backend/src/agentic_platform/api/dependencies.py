from __future__ import annotations

from typing import Annotated

from fastapi import Header, Request

from agentic_platform.auth.contracts import Principal
from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import UserId, WorkspaceId
from agentic_platform.domain.workspaces import MembershipRole


def application_dependencies(request: Request):
    return request.app.state.dependencies


def principal_from_headers(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    header_workspace_id: Annotated[str, Header(alias="X-Workspace-ID")],
    role: Annotated[str, Header(alias="X-Workspace-Role")],
) -> Principal:
    try:
        membership_role = MembershipRole(role)
    except ValueError as exc:
        raise DomainValidationError("workspace role is invalid") from exc
    return Principal(
        user_id=UserId.parse(user_id),
        workspace_id=WorkspaceId.parse(header_workspace_id),
        role=membership_role,
    )
