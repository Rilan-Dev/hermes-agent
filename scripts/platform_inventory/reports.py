from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import yaml

from .models import InventoryReport, SourceState

_REPORT_NAMES = (
    "source-state.json",
    "inventory.json",
    "extraction-manifest.yaml",
    "channel-capabilities.md",
    "provider-capabilities.md",
    "tool-capabilities.md",
    "frontend-api-map.md",
    "dependency-test-map.md",
    "phase-0-review.md",
)


def _primitive(value: Any) -> Any:
    if isinstance(value, SourceState):
        return {
            "root": ".",
            "branch": value.branch,
            "head_sha": value.head_sha,
            "dirty": value.dirty,
            "remotes": _primitive(value.remotes),
        }
    if dataclasses.is_dataclass(value):
        return {
            field.name: _primitive(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {
            str(key): _primitive(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_primitive(item) for item in value]
    return value


def blocking_findings(report: InventoryReport) -> tuple[str, ...]:
    findings: list[str] = []
    if report.source.dirty:
        findings.append("source worktree is dirty")
    findings.extend(
        f"runtime probe error: {error}" for error in report.registries.probe_errors
    )
    findings.extend(
        f"unresolved local import: {item}"
        for item in report.python_graph.unresolved_local_imports
    )
    return tuple(findings)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def _manifest(payload: dict[str, Any]) -> dict[str, Any]:
    files = payload["python_graph"]["files"]
    plugins = payload["plugins"]
    return {
        "version": payload["schema_version"],
        "source": {
            "branch": payload["source"]["branch"],
            "sha": payload["source"]["head_sha"],
            "remotes": payload["source"]["remotes"],
        },
        "include_roots": [
            {"source": "plugins", "class": "dynamic-plugin"},
            {"source": "gateway", "class": "core"},
            {"source": "providers", "class": "core"},
            {"source": "agent/transports", "class": "core"},
            {"source": "tools", "class": "tool-runtime"},
            {"source": "hermes_cli", "class": "host-runtime"},
            {"source": "web/src", "class": "frontend"},
            {"source": "apps/desktop/src", "class": "reference-frontend"},
        ],
        "plugins": [
            {
                "kind": plugin["kind"],
                "id": plugin["plugin_key"],
                "manifest": plugin["manifest_path"],
                "directory": plugin["directory"],
            }
            for plugin in plugins
        ],
        "files": [
            {
                "source": item["path"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "class": item["classification"],
            }
            for item in files
        ],
        "host_port_candidates": sorted(
            item["path"]
            for item in files
            if item["classification"] == "host-runtime"
        ),
        "unresolved_imports": payload["python_graph"]["unresolved_local_imports"],
        "runtime_probe_errors": payload["registries"]["probe_errors"],
    }


def _table(headers: tuple[str, ...], rows: list[tuple[Any, ...]]) -> str:
    if not rows:
        return "_None discovered._"
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = [
        "| "
        + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in row)
        + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _channel_markdown(payload: dict[str, Any]) -> str:
    platform_plugins = [
        plugin for plugin in payload["plugins"] if plugin["kind"] == "platform"
    ]
    runtime = set(payload["registries"]["platforms"])
    manifest_ids = {plugin["plugin_id"] for plugin in platform_plugins}
    rows = [
        (
            plugin["plugin_id"],
            plugin.get("label") or plugin["manifest_name"],
            "yes" if plugin["plugin_id"] in runtime else "no",
            ", ".join(plugin["required_env"]) or "—",
            ", ".join(plugin["optional_env"]) or "—",
            plugin["directory"],
        )
        for plugin in platform_plugins
    ]
    runtime_only = sorted(runtime - manifest_ids)
    manifest_only = sorted(manifest_ids - runtime)
    return "\n".join(
        [
            "# Channel Capability Inventory",
            "",
            _table(
                ("Channel", "Label", "Runtime", "Required env", "Optional env", "Source"),
                rows,
            ),
            "",
            "## Packaging differences",
            "",
            f"- Runtime-only/direct/legacy IDs: {', '.join(runtime_only) or 'None'}",
            f"- Manifest-only IDs: {', '.join(manifest_only) or 'None'}",
            f"- Concrete runtime entries: {', '.join(payload['registries']['platform_concrete']) or 'None'}",
            f"- Deferred runtime entries: {', '.join(payload['registries']['platform_deferred']) or 'None'}",
        ]
    )


def _provider_markdown(payload: dict[str, Any]) -> str:
    registries = payload["registries"]
    sets = (
        ("Provider profiles", registries["provider_profiles"]),
        ("Profile aliases", [f"{k} → {v}" for k, v in registries["provider_aliases"].items()]),
        ("Auth registry", registries["auth_providers"]),
        ("Canonical catalog", registries["canonical_providers"]),
        ("Model catalog keys", registries["model_catalog_providers"]),
        ("Transport API modes", registries["transports"]),
    )
    rows = [(name, len(values), ", ".join(values) or "—") for name, values in sets]
    service_rows = [
        (
            family,
            ", ".join(registries["service_provider_builtins"].get(family, [])) or "—",
            ", ".join(registries["service_provider_plugins"].get(family, [])) or "—",
            ", ".join(values) or "—",
        )
        for family, values in registries["service_providers"].items()
    ]
    all_ids: set[str] = set()
    for _, values in sets[:5]:
        for value in values:
            if " → " not in value:
                all_ids.add(value)
    membership_rows = []
    for identifier in sorted(all_ids):
        membership_rows.append(
            (
                identifier,
                "yes" if identifier in registries["provider_profiles"] else "",
                "yes" if identifier in registries["auth_providers"] else "",
                "yes" if identifier in registries["canonical_providers"] else "",
                "yes" if identifier in registries["model_catalog_providers"] else "",
            )
        )
    return "\n".join(
        [
            "# AI Provider Capability Inventory",
            "",
            "Provider identities remain separate until explicit compatibility rules map them.",
            "",
            _table(("Registry", "Count", "Identifiers"), rows),
            "",
            "## Tool-specific provider families",
            "",
            _table(("Family", "Built-in", "Plugin", "Combined"), service_rows),
            "",
            "## Cross-registry membership",
            "",
            _table(("ID", "Profile", "Auth", "Canonical", "Models"), membership_rows),
        ]
    )


def _tool_markdown(payload: dict[str, Any]) -> str:
    registries = payload["registries"]
    declared_plugin_tools = [
        (plugin["plugin_key"], tool)
        for plugin in payload["plugins"]
        for tool in plugin.get("provides_tools", [])
    ]
    registered = set(registries["tools"])
    declared_missing = [
        (plugin_key, tool)
        for plugin_key, tool in declared_plugin_tools
        if tool not in registered
    ]
    rows = []
    for name, tools in registries["toolsets"].items():
        rows.append(
            (
                name,
                ", ".join(registries["toolset_includes"].get(name, [])) or "—",
                len(tools),
                ", ".join(tools) or "—",
            )
        )
    tool_rows = [
        (name, registries["tool_to_toolset"].get(name, "unmapped"))
        for name in registries["tools"]
    ]
    return "\n".join(
        [
            "# Tool Capability Inventory",
            "",
            f"Registered tools: **{len(registries['tools'])}**",
            f"Imported built-in tool modules: **{len(registries['imported_tool_modules'])}**",
            "",
            "## Toolsets",
            "",
            _table(("Toolset", "Includes", "Direct count", "Direct tools"), rows),
            "",
            "## Registered tools",
            "",
            _table(("Tool", "Toolset"), tool_rows),
            "",
            "## Manifest-declared plugin tools",
            "",
            _table(("Plugin", "Tool"), declared_plugin_tools),
            "",
            "## Declared but not registered in isolated runtime",
            "",
            _table(("Plugin", "Tool"), declared_missing),
            "",
            "MCP tools are runtime-generated from configured servers and are therefore a registration path, not a fixed source list.",
        ]
    )


def _frontend_markdown(payload: dict[str, Any]) -> str:
    frontend = payload["frontend"]
    sections = (
        ("Browser routes", frontend["routes"]),
        ("REST API paths", frontend["api_paths"]),
        ("WebSocket paths", frontend["websocket_paths"]),
        ("Electron bridge references", frontend["electron_bridge_references"]),
        ("Static catalogs requiring parity checks", frontend["static_catalog_references"]),
    )
    return "\n".join(
        [
            "# Frontend and API Map",
            "",
            *[
                f"## {heading}\n\n" + ("\n".join(f"- `{item}`" for item in values) or "_None discovered._")
                for heading, values in sections
            ],
        ]
    )


def _dependency_markdown(payload: dict[str, Any]) -> str:
    dependencies = payload["dependencies"]
    extras = [
        (name, len(values), ", ".join(values) or "—")
        for name, values in dependencies["python_extras"].items()
    ]
    javascript = [
        (name, len(values), ", ".join(values) or "—")
        for name, values in dependencies["javascript_packages"].items()
    ]
    tests = [
        (name, len(values), "<br>".join(f"`{value}`" for value in values))
        for name, values in dependencies["tests_by_area"].items()
    ]
    return "\n".join(
        [
            "# Dependency and Test Map",
            "",
            f"Core Python requirements: **{len(dependencies['python_core'])}**",
            "",
            "## Python optional extras",
            "",
            _table(("Extra", "Count", "Requirements"), extras),
            "",
            "## JavaScript packages",
            "",
            _table(("Application", "Count", "Packages"), javascript),
            "",
            "## Tests by area",
            "",
            _table(("Area", "Count", "Files"), tests),
        ]
    )


def _review_markdown(report: InventoryReport, payload: dict[str, Any]) -> str:
    blockers = blocking_findings(report)
    manifest_platforms = {
        plugin["plugin_id"]
        for plugin in payload["plugins"]
        if plugin["kind"] == "platform"
    }
    runtime_platforms = set(payload["registries"]["platforms"])
    provider_sets_equal = (
        set(payload["registries"]["canonical_providers"])
        == set(payload["registries"]["auth_providers"])
        == set(payload["registries"]["provider_profiles"])
    )
    status = "BLOCKED" if blockers else "READY FOR REVIEW"
    lines = [
        "# Phase 0 Review",
        "",
        f"**Status:** {status}",
        f"**Source:** `{payload['source']['branch']}@{payload['source']['head_sha']}`",
        "",
        "## Blocking findings",
        "",
    ]
    lines.extend(f"- {item}" for item in blockers)
    if not blockers:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Plugin manifests: {len(payload['plugins'])}",
            f"- Runtime channels: {len(runtime_platforms)}",
            f"- Channel manifest/runtime differences: {len(manifest_platforms ^ runtime_platforms)}",
            f"- Canonical providers: {len(payload['registries']['canonical_providers'])}",
            f"- Provider identifier sets identical: {'yes' if provider_sets_equal else 'no — expected, review mappings'}",
            f"- Registered tools: {len(payload['registries']['tools'])}",
            f"- Frontend routes: {len(payload['frontend']['routes'])}",
            f"- Electron bridge references: {len(payload['frontend']['electron_bridge_references'])}",
            f"- Scoped Python files: {len(payload['python_graph']['files'])}",
            "",
            "## Phase 1 gate",
            "",
            "Do not start the inbox schema or renderer implementation until blockers are cleared and the generated manifest/capability reports are reviewed.",
        ]
    )
    return "\n".join(lines)


def write_reports(report: InventoryReport, output: Path) -> tuple[Path, ...]:
    payload = _primitive(report)
    files = {
        "source-state.json": json.dumps(payload["source"], indent=2, sort_keys=True),
        "inventory.json": json.dumps(payload, indent=2, sort_keys=True),
        "extraction-manifest.yaml": yaml.safe_dump(
            _manifest(payload), sort_keys=True, allow_unicode=True
        ),
        "channel-capabilities.md": _channel_markdown(payload),
        "provider-capabilities.md": _provider_markdown(payload),
        "tool-capabilities.md": _tool_markdown(payload),
        "frontend-api-map.md": _frontend_markdown(payload),
        "dependency-test-map.md": _dependency_markdown(payload),
        "phase-0-review.md": _review_markdown(report, payload),
    }
    return tuple(_write(output / name, files[name]) for name in _REPORT_NAMES)
