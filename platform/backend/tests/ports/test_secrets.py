from dataclasses import fields
from datetime import datetime, timezone

from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.ports.secrets import SecretDescriptor, SecretReference


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)


def test_secret_descriptor_exposes_reference_metadata_not_secret_material() -> None:
    descriptor = SecretDescriptor.create(
        workspace_id=WorkspaceId.new(),
        reference=SecretReference.parse("secret_provider_openai"),
        label="OpenAI production key",
        provider="openai-api",
        created_at=NOW,
    )

    names = {field.name for field in fields(descriptor)}
    forbidden = {"value", "secret", "token", "api_key", "credentials"}

    assert names.isdisjoint(forbidden)
    assert "sk-secret-material" not in repr(descriptor)
