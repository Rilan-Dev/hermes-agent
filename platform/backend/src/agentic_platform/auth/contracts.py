from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import UserId, WorkspaceId
from agentic_platform.domain.workspaces import MembershipRole


class Permission(StrEnum):
    WORKSPACE_ADMIN = "workspace.admin"
    PROVIDER_CONFIGURE = "provider.configure"
    SECRET_MANAGE = "secret.manage"
    CHANNEL_MANAGE = "channel.manage"
    INBOX_READ = "inbox.read"
    INBOX_WRITE = "inbox.write"
    AGENT_CONTROL = "agent.control"
    TOOL_APPROVE = "tool.approve"
    AUDIT_READ = "audit.read"


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: UserId
    workspace_id: WorkspaceId
    role: MembershipRole

    def __post_init__(self) -> None:
        if not isinstance(self.user_id, UserId):
            raise DomainValidationError("principal user ID is invalid")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise DomainValidationError("principal workspace ID is invalid")
        if not isinstance(self.role, MembershipRole):
            raise DomainValidationError("principal membership role is invalid")
