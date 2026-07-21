from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .errors import CrossWorkspaceError, DomainValidationError
from .ids import ConnectionId, ContactId, ExternalIdentityId, WorkspaceId
from .time import require_utc


def _required_text(value: str, *, field: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise DomainValidationError(f"{field} must not be blank")
    return normalized


@dataclass(frozen=True, slots=True)
class NativeReference:
    platform_id: str
    native_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "platform_id",
            _required_text(self.platform_id, field="platform ID"),
        )
        object.__setattr__(
            self,
            "native_id",
            _required_text(self.native_id, field="native ID"),
        )


@dataclass(frozen=True, slots=True)
class ChannelConnection:
    id: ConnectionId
    workspace_id: WorkspaceId
    platform_id: str
    display_name: str
    created_at: datetime
    secret_ref: str | None = None

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        platform_id: str,
        display_name: str,
        created_at: datetime,
        secret_ref: str | None = None,
    ) -> ChannelConnection:
        normalized_secret = secret_ref.strip() if isinstance(secret_ref, str) else None
        if secret_ref is not None and not normalized_secret:
            raise DomainValidationError("secret reference must not be blank")
        return cls(
            id=ConnectionId.new(),
            workspace_id=workspace_id,
            platform_id=_required_text(platform_id, field="platform ID"),
            display_name=_required_text(display_name, field="connection display name"),
            created_at=require_utc(created_at, field="connection created_at"),
            secret_ref=normalized_secret,
        )


@dataclass(frozen=True, slots=True)
class ExternalIdentity:
    id: ExternalIdentityId
    workspace_id: WorkspaceId
    connection_id: ConnectionId
    contact_id: ContactId
    native: NativeReference
    created_at: datetime
    display_name: str | None = None

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        connection: ChannelConnection,
        contact_id: ContactId,
        native: NativeReference,
        created_at: datetime,
        display_name: str | None = None,
    ) -> ExternalIdentity:
        if workspace_id != connection.workspace_id:
            raise CrossWorkspaceError(
                "external identity and channel connection must share a workspace"
            )
        if native.platform_id != connection.platform_id:
            raise DomainValidationError(
                "external identity platform must match the channel connection"
            )
        normalized_name = display_name.strip() if isinstance(display_name, str) else None
        return cls(
            id=ExternalIdentityId.new(),
            workspace_id=workspace_id,
            connection_id=connection.id,
            contact_id=contact_id,
            native=native,
            created_at=require_utc(created_at, field="external identity created_at"),
            display_name=normalized_name or None,
        )
