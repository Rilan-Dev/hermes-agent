from datetime import datetime, timezone

import pytest

from agentic_platform.domain.channels import (
    ChannelConnection,
    ExternalIdentity,
    NativeReference,
)
from agentic_platform.domain.errors import CrossWorkspaceError, DomainValidationError
from agentic_platform.domain.ids import ContactId, UserId, WorkspaceId
from agentic_platform.domain.workspaces import Membership, MembershipRole, Workspace


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)


def test_workspace_and_membership_are_immutable_and_validated() -> None:
    workspace = Workspace.create(name="Acme Support", created_at=NOW)
    membership = Membership.create(
        workspace_id=workspace.id,
        user_id=UserId.new(),
        role=MembershipRole.OPERATOR,
        created_at=NOW,
    )

    assert workspace.name == "Acme Support"
    assert membership.workspace_id == workspace.id
    assert membership.role is MembershipRole.OPERATOR

    with pytest.raises(DomainValidationError, match="workspace name"):
        Workspace.create(name="   ", created_at=NOW)


def test_native_reference_rejects_blank_platform_or_native_id() -> None:
    with pytest.raises(DomainValidationError, match="platform ID"):
        NativeReference(platform_id=" ", native_id="123")
    with pytest.raises(DomainValidationError, match="native ID"):
        NativeReference(platform_id="telegram", native_id=" ")


def test_external_identity_rejects_cross_workspace_connection() -> None:
    connection = ChannelConnection.create(
        workspace_id=WorkspaceId.new(),
        platform_id="telegram",
        display_name="Support Bot",
        created_at=NOW,
    )

    with pytest.raises(CrossWorkspaceError):
        ExternalIdentity.create(
            workspace_id=WorkspaceId.new(),
            connection=connection,
            contact_id=ContactId.new(),
            native=NativeReference("telegram", "user-42"),
            created_at=NOW,
        )
