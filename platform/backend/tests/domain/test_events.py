from datetime import datetime, timezone

import pytest

from agentic_platform.domain.channels import ChannelConnection, NativeReference
from agentic_platform.domain.errors import CrossWorkspaceError, DomainValidationError
from agentic_platform.domain.events import ChannelEvent, ChannelEventKind
from agentic_platform.domain.ids import WorkspaceId


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)


def test_channel_event_exposes_workspace_scoped_idempotency_key() -> None:
    connection = ChannelConnection.create(
        workspace_id=WorkspaceId.new(),
        platform_id="telegram",
        display_name="Support Bot",
        created_at=NOW,
    )
    event = ChannelEvent.create(
        workspace_id=connection.workspace_id,
        connection=connection,
        platform_event_id="update-123",
        kind=ChannelEventKind.MESSAGE,
        occurred_at=NOW,
        native_target=NativeReference("telegram", "message-456"),
    )

    assert event.idempotency_key == (
        connection.workspace_id,
        connection.id,
        "update-123",
    )


def test_channel_event_rejects_blank_event_id_and_cross_workspace() -> None:
    connection = ChannelConnection.create(
        workspace_id=WorkspaceId.new(),
        platform_id="telegram",
        display_name="Support Bot",
        created_at=NOW,
    )

    with pytest.raises(DomainValidationError, match="platform event ID"):
        ChannelEvent.create(
            workspace_id=connection.workspace_id,
            connection=connection,
            platform_event_id=" ",
            kind=ChannelEventKind.MESSAGE,
            occurred_at=NOW,
        )

    with pytest.raises(CrossWorkspaceError):
        ChannelEvent.create(
            workspace_id=WorkspaceId.new(),
            connection=connection,
            platform_event_id="update-124",
            kind=ChannelEventKind.RECEIPT,
            occurred_at=NOW,
        )
