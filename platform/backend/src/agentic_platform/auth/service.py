from __future__ import annotations

from agentic_platform.auth.contracts import Permission, Principal
from agentic_platform.auth.policies import is_allowed
from agentic_platform.domain.errors import DomainError
from agentic_platform.domain.ids import WorkspaceId


class ResourceNotFound(DomainError):
    """Not-found-safe denial used for cross-workspace access."""


class AuthorizationDenied(DomainError):
    """Raised when a principal lacks a permission in its active workspace."""


class AuthorizationService:
    def require(
        self,
        principal: Principal,
        permission: Permission,
        *,
        resource_workspace_id: WorkspaceId,
    ) -> Principal:
        if resource_workspace_id != principal.workspace_id:
            raise ResourceNotFound("resource was not found")
        if not is_allowed(principal, permission):
            raise AuthorizationDenied(
                f"permission {permission.value} is required"
            )
        return principal
