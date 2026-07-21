from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .models import InventoryError, RegistrySnapshot

_REQUIRED_FIELDS = {
    "platforms",
    "platform_concrete",
    "platform_deferred",
    "provider_profiles",
    "provider_aliases",
    "auth_providers",
    "canonical_providers",
    "model_catalog_providers",
    "transports",
    "toolsets",
    "toolset_includes",
    "tools",
    "tool_to_toolset",
    "imported_tool_modules",
    "probe_errors",
}


def _string_tuple(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload[field]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise InventoryError(f"{field} must be an array of strings")
    return tuple(sorted(set(value)))


def _string_map(payload: dict[str, Any], field: str) -> dict[str, str]:
    value = payload[field]
    if not isinstance(value, dict):
        raise InventoryError(f"{field} must be an object")
    if not all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()):
        raise InventoryError(f"{field} must map strings to strings")
    return dict(sorted(value.items()))


def _toolset_map(payload: dict[str, Any], field: str) -> dict[str, tuple[str, ...]]:
    value = payload[field]
    if not isinstance(value, dict):
        raise InventoryError(f"{field} must be an object")
    result: dict[str, tuple[str, ...]] = {}
    for key, items in value.items():
        if not isinstance(key, str) or not isinstance(items, list) or not all(
            isinstance(item, str) for item in items
        ):
            raise InventoryError(f"{field} must map strings to arrays of strings")
        result[key] = tuple(sorted(set(items)))
    return dict(sorted(result.items()))


def parse_probe_output(stdout: str) -> RegistrySnapshot:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise InventoryError("invalid runtime probe JSON") from exc
    if not isinstance(payload, dict):
        raise InventoryError("runtime probe payload must be an object")

    missing = sorted(_REQUIRED_FIELDS - set(payload))
    if missing:
        raise InventoryError(f"runtime probe missing keys: {', '.join(missing)}")

    return RegistrySnapshot(
        platforms=_string_tuple(payload, "platforms"),
        platform_concrete=_string_tuple(payload, "platform_concrete"),
        platform_deferred=_string_tuple(payload, "platform_deferred"),
        provider_profiles=_string_tuple(payload, "provider_profiles"),
        provider_aliases=_string_map(payload, "provider_aliases"),
        auth_providers=_string_tuple(payload, "auth_providers"),
        canonical_providers=_string_tuple(payload, "canonical_providers"),
        model_catalog_providers=_string_tuple(payload, "model_catalog_providers"),
        transports=_string_tuple(payload, "transports"),
        toolsets=_toolset_map(payload, "toolsets"),
        toolset_includes=_toolset_map(payload, "toolset_includes"),
        tools=_string_tuple(payload, "tools"),
        tool_to_toolset=_string_map(payload, "tool_to_toolset"),
        imported_tool_modules=_string_tuple(payload, "imported_tool_modules"),
        probe_errors=_string_tuple(payload, "probe_errors"),
    )


def probe_runtime(root: Path, timeout_seconds: float = 45) -> RegistrySnapshot:
    repository = root.resolve()
    with tempfile.TemporaryDirectory(prefix="hermes-inventory-") as home:
        env = os.environ.copy()
        env.update(
            {
                "HERMES_HOME": home,
                "HERMES_PROFILE": "inventory",
                "HERMES_INVENTORY_MODE": "1",
                "HERMES_ENABLE_PROJECT_PLUGINS": "0",
                "HERMES_PLUGINS_DEBUG": "0",
                "PYTHONPATH": os.pathsep.join(
                    [str(repository), env.get("PYTHONPATH", "")]
                ).rstrip(os.pathsep),
            }
        )
        result = subprocess.run(
            [sys.executable, "-m", "scripts.platform_inventory.probe_entrypoint"],
            cwd=repository,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise InventoryError(f"runtime probe failed: {detail}")
    return parse_probe_output(result.stdout)
