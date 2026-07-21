from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class InventoryError(RuntimeError):
    """Raised when Phase 0 cannot produce a trustworthy inventory."""


@dataclass(frozen=True, slots=True)
class SourceState:
    root: Path
    branch: str
    head_sha: str
    dirty: bool
    remotes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["root"] = str(self.root)
        return data


@dataclass(frozen=True, slots=True)
class PluginRecord:
    kind: str
    plugin_id: str
    manifest_name: str
    label: str | None
    version: str | None
    description: str | None
    manifest_path: str
    directory: str
    entrypoints: tuple[str, ...]
    required_env: tuple[str, ...]
    optional_env: tuple[str, ...]
    optional_dependencies: tuple[str, ...]
    files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FileRecord:
    path: str
    sha256: str
    size_bytes: int
    classification: str


@dataclass(frozen=True, slots=True)
class ImportEdge:
    source: str
    module: str
    target: str | None


@dataclass(frozen=True, slots=True)
class PythonGraph:
    files: tuple[FileRecord, ...]
    imports: tuple[ImportEdge, ...]
    dynamic_imports: tuple[str, ...]
    unresolved_local_imports: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    platforms: tuple[str, ...]
    platform_concrete: tuple[str, ...]
    platform_deferred: tuple[str, ...]
    provider_profiles: tuple[str, ...]
    provider_aliases: dict[str, str]
    auth_providers: tuple[str, ...]
    canonical_providers: tuple[str, ...]
    model_catalog_providers: tuple[str, ...]
    transports: tuple[str, ...]
    toolsets: dict[str, tuple[str, ...]]
    toolset_includes: dict[str, tuple[str, ...]]
    tools: tuple[str, ...]
    tool_to_toolset: dict[str, str]
    imported_tool_modules: tuple[str, ...]
    probe_errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrontendMap:
    routes: tuple[str, ...]
    api_paths: tuple[str, ...]
    websocket_paths: tuple[str, ...]
    electron_bridge_references: tuple[str, ...]
    static_catalog_references: tuple[str, ...]
