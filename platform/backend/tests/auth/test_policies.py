from __future__ import annotations

import pytest

from agentic_platform.auth.contracts import Permission, Principal
from agentic_platform.auth.policies import allowed_permissions, is_allowed
from agentic_platform.auth.service import (
    AuthorizationDenied,
    AuthorizationService,
    ResourceNotFound,
)
from agentic_platform.domain.ids import UserId, WorkspaceId
from agentic_platform.domain.workspaces import MembershipRole


def _principal(role: MembershipRole) -> Principal:
    return Principal(
        user_id=UserId.new(),
        workspace_id=WorkspaceId.new(),
        role=role,
    )


def test_permissions_are_deny_by_default_and_role_sets_are_immutable() -> None:
    viewer = _principal(MembershipRole.VIEWER)

    assert allowed_permissions(MembershipRole.VIEWER) == frozenset(
        {Permission.INBOX_READ, Permission.AUDIT_READ}
    )
    assert is_allowed(viewer, Permission.INBOX_READ) is True
    assert is_allowed(viewer, Permission.INBOX_WRITE) is False


def test_owner_admin_operator_developer_permissions_are_explicit() -> None:
    owner = _principal(MembershipRole.OWNER)
    admin = _principal(MembershipRole.ADMIN)
    operator = _principal(MembershipRole.OPERATOR)
    developer = _principal(MembershipRole.DEVELOPER)

    assert allowed_permissions(MembershipRole.OWNER) == frozenset(Permission)
    assert allowed_permissions(MembershipRole.ADMIN) == frozenset(Permission)
    assert is_allowed(operator, Permission.INBOX_WRITE) is True
    assert is_allowed(operator, Permission.SECRET_MANAGE) is False
    assert is_allowed(developer, Permission.PROVIDER_CONFIGURE) is True
    assert is_allowed(developer, Permission.TOOL_APPROVE) is False


def test_authorization_service_uses_not_found_safe_cross_workspace_denial() -> None:
    service = AuthorizationService()
    principal = _principal(MembershipRole.ADMIN)

    with pytest.raises(ResourceNotFound):
        service.require(
            principal,
            Permission.WORKSPACE_ADMIN,
            resource_workspace_id=WorkspaceId.new(),
        )


def test_authorization_service_distinguishes_same_workspace_permission_denial() -> None:
    service = AuthorizationService()
    principal = _principal(MembershipRole.VIEWER)

    with pytest.raises(AuthorizationDenied, match="inbox.write"):
        service.require(
            principal,
            Permission.INBOX_WRITE,
            resource_workspace_id=principal.workspace_id,
        )


def test_authorization_service_returns_principal_on_success() -> None:
    service = AuthorizationService()
    principal = _principal(MembershipRole.OPERATOR)

    assert (
        service.require(
            principal,
            Permission.INBOX_WRITE,
            resource_workspace_id=principal.workspace_id,
        )
        is principal
    )
