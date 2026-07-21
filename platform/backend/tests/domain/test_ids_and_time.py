from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import ConversationId, WorkspaceId
from agentic_platform.domain.time import require_utc, utc_now


def test_entity_ids_are_strong_uuid_backed_types() -> None:
    workspace_id = WorkspaceId.new()
    parsed = WorkspaceId.parse(str(workspace_id))

    assert isinstance(workspace_id.value, UUID)
    assert parsed == workspace_id
    assert type(parsed) is WorkspaceId
    assert WorkspaceId.parse(workspace_id.value) == workspace_id
    assert WorkspaceId.parse(str(workspace_id)) != ConversationId.parse(str(workspace_id))


def test_entity_id_parse_rejects_invalid_uuid() -> None:
    with pytest.raises(DomainValidationError, match="valid UUID"):
        WorkspaceId.parse("not-a-uuid")


def test_require_utc_rejects_naive_datetimes() -> None:
    with pytest.raises(DomainValidationError, match="timezone-aware"):
        require_utc(datetime(2026, 7, 21, 10, 0, 0))


def test_require_utc_normalizes_offsets() -> None:
    india = timezone(timedelta(hours=5, minutes=30))
    value = require_utc(datetime(2026, 7, 21, 15, 30, tzinfo=india))

    assert value == datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)
    assert value.tzinfo is timezone.utc
    assert utc_now().tzinfo is timezone.utc
