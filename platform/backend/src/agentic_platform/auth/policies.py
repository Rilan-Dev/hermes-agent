from __future__ import annotations

from agentic_platform.auth.contracts import Permission, Principal
from agentic_platform.domain.workspaces import MembershipRole


_ALL = frozenset(Permission)
_ROLE_PERMISSIONS: dict[MembershipRole, frozenset[Permission]] = {
    MembershipRole.OWNER: _ALL,
    MembershipRole.ADMIN: _ALL,
    MembershipRole.OPERATOR: frozenset(
        {
            Permission.CHANNEL_MANAGE,
            Permission.INBOX_READ,
            Permission.INBOX_WRITE,
            Permission.AGENT_CONTROL,
            Permission.TOOL_APPROVE,
            Permission.AUDIT_READ,
        }
    ),
    MembershipRole.DEVELOPER: frozenset(
        {
            Permission.PROVIDER_CONFIGURE,
            Permission.SECRET_MANAGE,
            Permission.CHANNEL_MANAGE,
            Permission.INBOX_READ,
            Permission.AGENT_CONTROL,
            Permission.AUDIT_READ,
        }
    ),
    MembershipRole.VIEWER: frozenset(
        {Permission.INBOX_READ, Permission.AUDIT_READ}
    ),
}


def allowed_permissions(role: MembershipRole) -> frozenset[Permission]:
    return _ROLE_PERMISSIONS.get(role, frozenset())


def is_allowed(principal: Principal, permission: Permission) -> bool:
    return permission in allowed_permissions(principal.role)
