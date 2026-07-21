from datetime import datetime, timezone

import pytest

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import ConversationId, EventId, WorkspaceId
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)


def test_event_cursor_is_monotonic_non_negative_value() -> None:
    assert EventCursor(0).next() == EventCursor(1)
    assert EventCursor.parse("42") == EventCursor(42)

    with pytest.raises(DomainValidationError, match="non-negative"):
        EventCursor(-1)


def test_workspace_event_copies_payload_and_requires_utc() -> None:
    payload = {"message_id": "m-1"}
    event = WorkspaceEvent.create(
        workspace_id=WorkspaceId.new(),
        cursor=EventCursor(1),
        event_id=EventId.new(),
        aggregate_type="conversation",
        aggregate_id=str(ConversationId.new()),
        event_type="conversation.message.created",
        payload=payload,
        occurred_at=NOW,
    )
    payload["message_id"] = "changed"

    assert event.payload["message_id"] == "m-1"
    with pytest.raises(TypeError):
        event.payload["new"] = "not allowed"  # type: ignore[index]

    with pytest.raises(DomainValidationError, match="timezone-aware"):
        WorkspaceEvent.create(
            workspace_id=WorkspaceId.new(),
            cursor=EventCursor(1),
            event_id=EventId.new(),
            aggregate_type="conversation",
            aggregate_id="c-1",
            event_type="conversation.updated",
            payload={},
            occurred_at=datetime(2026, 7, 21, 10, 0),
        )
