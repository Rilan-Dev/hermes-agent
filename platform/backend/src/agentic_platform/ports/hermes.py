from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, Sequence

from agentic_platform.domain.errors import DomainValidationError


def _required_text(value: str, *, field_name: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise DomainValidationError(f"{field_name} must not be blank")
    return normalized


class DescriptorSource(StrEnum):
    BUILTIN = "builtin"
    PLUGIN = "plugin"
    USER_PLUGIN = "user_plugin"
    DYNAMIC = "dynamic"


class ProviderIdentityKind(StrEnum):
    PROFILE = "profile"
    AUTH = "auth"
    CANONICAL = "canonical"
    MODEL_CATALOG = "model_catalog"
    TRANSPORT = "transport"
    SERVICE = "service"


@dataclass(frozen=True, slots=True)
class ChannelDescriptor:
    platform_id: str
    display_name: str
    source: DescriptorSource
    capabilities: frozenset[str] = field(default_factory=frozenset)
    deferred: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "platform_id",
            _required_text(self.platform_id, field_name="platform ID"),
        )
        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, field_name="channel display name"),
        )
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    provider_id: str
    display_name: str
    identity_kind: ProviderIdentityKind
    aliases: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_id",
            _required_text(self.provider_id, field_name="provider ID"),
        )
        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, field_name="provider display name"),
        )
        object.__setattr__(self, "aliases", frozenset(self.aliases))


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    name: str
    toolset: str
    source: DescriptorSource
    risk_class: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_text(self.name, field_name="tool name"))
        object.__setattr__(self, "toolset", _required_text(self.toolset, field_name="toolset"))
        object.__setattr__(
            self,
            "risk_class",
            _required_text(self.risk_class, field_name="risk class"),
        )


class HermesCatalog(Protocol):
    async def list_channels(self) -> Sequence[ChannelDescriptor]: ...

    async def list_providers(self) -> Sequence[ProviderDescriptor]: ...

    async def list_tools(self) -> Sequence[ToolDescriptor]: ...

    async def ready(self) -> bool: ...
