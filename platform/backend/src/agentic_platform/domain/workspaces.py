from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .errors import DomainValidationError
from .ids import UserId, WorkspaceId
from .time import require_utc


class MembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    DEVELOPER = "developer"
    VIEWER = "viewer"


def _required_text(value: str, *, field: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise DomainValidationError(f"{field} must not be blank")
    return normalized


@dataclass(frozen=True, slots=True)
class Workspace:
    id: WorkspaceId
    name: str
    created_at: datetime

    @classmethod
    def create(cls, *, name: str, created_at: datetime) -> Workspace:
        return cls(
            id=WorkspaceId.new(),
            name=_required_text(name, field="workspace name"),
            created_at=require_utc(created_at, field="workspace created_at"),
        )


@dataclass(frozen=True, slots=True)
class Membership:
    workspace_id: WorkspaceId
    user_id: UserId
    role: MembershipRole
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        user_id: UserId,
        role: MembershipRole,
        created_at: datetime,
    ) -> Membership:
        if not isinstance(role, MembershipRole):
            raise DomainValidationError("membership role is invalid")
        return cls(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            created_at=require_utc(created_at, field="membership created_at"),
        )
