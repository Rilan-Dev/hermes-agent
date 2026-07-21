from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from .errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class EntityId:
    """Strong, immutable UUID-backed identifier."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise DomainValidationError(f"{type(self).__name__} value must be a UUID")

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())

    @classmethod
    def parse(cls, value: str | UUID | EntityId) -> Self:
        if isinstance(value, cls):
            return value
        raw = value.value if isinstance(value, EntityId) else value
        try:
            parsed = raw if isinstance(raw, UUID) else UUID(str(raw))
        except (TypeError, ValueError, AttributeError) as exc:
            raise DomainValidationError(
                f"{type(value).__name__} is not a valid UUID for {cls.__name__}"
            ) from exc
        return cls(parsed)

    def __str__(self) -> str:
        return str(self.value)


class WorkspaceId(EntityId):
    pass


class UserId(EntityId):
    pass


class AgentId(EntityId):
    pass


class ConnectionId(EntityId):
    pass


class ContactId(EntityId):
    pass


class ExternalIdentityId(EntityId):
    pass


class ConversationId(EntityId):
    pass


class MessageId(EntityId):
    pass


class EventId(EntityId):
    pass


class AttachmentId(EntityId):
    pass


class RunId(EntityId):
    pass
