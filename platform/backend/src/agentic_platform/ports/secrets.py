from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.domain.time import require_utc


def _required_text(value: str, *, field: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise DomainValidationError(f"{field} must not be blank")
    return normalized


@dataclass(frozen=True, slots=True)
class SecretReference:
    value: str

    @classmethod
    def parse(cls, value: str | SecretReference) -> SecretReference:
        if isinstance(value, cls):
            return value
        return cls(_required_text(value, field="secret reference"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SecretDescriptor:
    workspace_id: WorkspaceId
    reference: SecretReference
    label: str
    provider: str | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        reference: SecretReference,
        label: str,
        provider: str | None,
        created_at: datetime,
    ) -> SecretDescriptor:
        normalized_provider = provider.strip() if isinstance(provider, str) else None
        return cls(
            workspace_id=workspace_id,
            reference=reference,
            label=_required_text(label, field="secret label"),
            provider=normalized_provider or None,
            created_at=require_utc(created_at, field="secret created_at"),
        )


class SecretStore(Protocol):
    async def store(
        self,
        workspace_id: WorkspaceId,
        *,
        label: str,
        provider: str | None,
        material: bytes,
    ) -> SecretDescriptor: ...

    async def describe(
        self,
        workspace_id: WorkspaceId,
        reference: SecretReference,
    ) -> SecretDescriptor | None: ...

    async def delete(
        self,
        workspace_id: WorkspaceId,
        reference: SecretReference,
    ) -> None: ...
