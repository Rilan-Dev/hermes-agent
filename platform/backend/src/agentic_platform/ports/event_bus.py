from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping, Protocol, Sequence

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import EventId, WorkspaceId
from agentic_platform.domain.time import require_utc


def _required_text(value: str, *, field: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise DomainValidationError(f"{field} must not be blank")
    return normalized


@dataclass(frozen=True, slots=True, order=True)
class EventCursor:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise DomainValidationError("event cursor must be an integer")
        if self.value < 0:
            raise DomainValidationError("event cursor must be non-negative")

    @classmethod
    def parse(cls, value: str | int | EventCursor) -> EventCursor:
        if isinstance(value, cls):
            return value
        try:
            return cls(int(value))
        except (TypeError, ValueError) as exc:
            raise DomainValidationError("event cursor must be an integer") from exc

    def next(self) -> EventCursor:
        return EventCursor(self.value + 1)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class WorkspaceEvent:
    workspace_id: WorkspaceId
    cursor: EventCursor
    event_id: EventId
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: Mapping[str, Any]
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        cursor: EventCursor,
        event_id: EventId,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: Mapping[str, Any],
        occurred_at: datetime,
    ) -> WorkspaceEvent:
        if not isinstance(payload, Mapping):
            raise DomainValidationError("workspace event payload must be a mapping")
        return cls(
            workspace_id=workspace_id,
            cursor=cursor,
            event_id=event_id,
            aggregate_type=_required_text(aggregate_type, field="aggregate type"),
            aggregate_id=_required_text(aggregate_id, field="aggregate ID"),
            event_type=_required_text(event_type, field="event type"),
            payload=MappingProxyType(dict(payload)),
            occurred_at=require_utc(occurred_at, field="workspace event occurred_at"),
        )


class WorkspaceEventPublisher(Protocol):
    async def publish(
        self,
        workspace_id: WorkspaceId,
        events: Sequence[WorkspaceEvent],
    ) -> None: ...


class WorkspaceEventStream(Protocol):
    async def read(
        self,
        workspace_id: WorkspaceId,
        *,
        after: EventCursor | None,
        limit: int,
    ) -> Sequence[WorkspaceEvent]: ...
