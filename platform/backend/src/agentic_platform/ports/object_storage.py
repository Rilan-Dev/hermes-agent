from __future__ import annotations

import re
from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import Protocol

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import WorkspaceId


_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def _required_text(value: str, *, field: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise DomainValidationError(f"{field} must not be blank")
    return normalized


@dataclass(frozen=True, slots=True)
class ObjectReference:
    value: str

    @classmethod
    def parse(cls, value: str | ObjectReference) -> ObjectReference:
        if isinstance(value, cls):
            return value
        return cls(_required_text(value, field="object reference"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    filename: str
    content_type: str
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "filename", _required_text(self.filename, field="filename"))
        object.__setattr__(
            self,
            "content_type",
            _required_text(self.content_type, field="content type"),
        )
        if not isinstance(self.size_bytes, int) or isinstance(self.size_bytes, bool):
            raise DomainValidationError("object size must be an integer")
        if self.size_bytes < 0:
            raise DomainValidationError("object size must be non-negative")
        normalized_digest = self.sha256.lower() if isinstance(self.sha256, str) else ""
        if not _SHA256.fullmatch(normalized_digest):
            raise DomainValidationError("object SHA-256 must be 64 hexadecimal characters")
        object.__setattr__(self, "sha256", normalized_digest)


@dataclass(frozen=True, slots=True)
class StoredObject:
    workspace_id: WorkspaceId
    reference: ObjectReference
    metadata: ObjectMetadata


class ObjectStorage(Protocol):
    async def put(
        self,
        workspace_id: WorkspaceId,
        *,
        data: AsyncIterable[bytes],
        metadata: ObjectMetadata,
    ) -> StoredObject: ...

    async def metadata(
        self,
        workspace_id: WorkspaceId,
        reference: ObjectReference,
    ) -> ObjectMetadata | None: ...

    async def delete(
        self,
        workspace_id: WorkspaceId,
        reference: ObjectReference,
    ) -> None: ...
