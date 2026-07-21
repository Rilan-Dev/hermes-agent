from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, Callable


def _sorted_strings(values: Any) -> list[str]:
    if values is None:
        return []
    return sorted({str(value) for value in values})


def _mapping_keys(value: Any) -> list[str]:
    return _sorted_strings(value.keys()) if isinstance(value, Mapping) else []


def _record_error(payload: dict[str, Any], section: str, exc: BaseException) -> None:
    text = str(exc).replace("\n", " ").strip()
    payload["probe_errors"].append(
        f"{section}:{type(exc).__name__}:{text or 'no detail'}"
    )


def _capture(payload: dict[str, Any], section: str, callback: Callable[[], None]) -> None:
    try:
        callback()
    except BaseException as exc:
        _record_error(payload, section, exc)


def collect_snapshot() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "platforms": [],
        "platform_concrete": [],
        "platform_deferred": [],
        "provider_profiles": [],
        "provider_aliases": {},
        "auth_providers": [],
        "canonical_providers": [],
        "model_catalog_providers": [],
        "transports": [],
        "service_providers": {},
        "service_provider_builtins": {},
        "service_provider_plugins": {},
        "toolsets": {},
        "toolset_includes": {},
        "tools": [],
        "tool_to_toolset": {},
        "imported_tool_modules": [],
        "probe_errors": [],
    }

    def platforms() -> None:
        from hermes_cli.plugins import PluginManager

        manager = PluginManager()
        manager.discover_and_load()

        from gateway.platform_registry import platform_registry

        concrete = _mapping_keys(getattr(platform_registry, "_entries", {}))
        deferred = _mapping_keys(getattr(platform_registry, "_deferred", {}))
        payload["platform_concrete"] = concrete
        payload["platform_deferred"] = deferred
        payload["platforms"] = sorted(set(concrete) | set(deferred))

    def providers() -> None:
        import providers as provider_module

        profiles = provider_module.list_providers()
        payload["provider_profiles"] = _sorted_strings(
            getattr(profile, "name", "")
            for profile in profiles
            if getattr(profile, "name", "")
        )
        aliases = getattr(provider_module, "_ALIASES", {})
        if isinstance(aliases, Mapping):
            payload["provider_aliases"] = {
                str(key): str(value) for key, value in sorted(aliases.items())
            }

    def auth_providers() -> None:
        from hermes_cli.auth import PROVIDER_REGISTRY

        payload["auth_providers"] = _mapping_keys(PROVIDER_REGISTRY)

    def canonical_providers() -> None:
        from hermes_cli.provider_catalog import provider_catalog

        payload["canonical_providers"] = _sorted_strings(
            descriptor.slug for descriptor in provider_catalog()
        )

    def model_catalog() -> None:
        from hermes_cli import models

        payload["model_catalog_providers"] = _mapping_keys(
            getattr(models, "_PROVIDER_MODELS", {})
        )

    def transports() -> None:
        import agent.transports as transport_module

        transport_module._discover_transports()
        payload["transports"] = _mapping_keys(
            getattr(transport_module, "_REGISTRY", {})
        )

    def service_providers() -> None:
        import importlib

        families = (
            ("image_gen", "agent.image_gen_registry"),
            ("video_gen", "agent.video_gen_registry"),
            ("tts", "agent.tts_registry"),
            ("stt", "agent.transcription_registry"),
            ("browser", "agent.browser_registry"),
            ("web", "agent.web_search_registry"),
        )
        combined: dict[str, list[str]] = {}
        builtins: dict[str, list[str]] = {}
        plugins: dict[str, list[str]] = {}

        for family, module_name in families:
            module = importlib.import_module(module_name)
            list_fn = getattr(module, "list_providers", None)
            registered = (
                _sorted_strings(
                    getattr(provider, "name", "")
                    for provider in list_fn()
                    if getattr(provider, "name", "")
                )
                if callable(list_fn)
                else []
            )
            builtin_names = _sorted_strings(getattr(module, "_BUILTIN_NAMES", ()))
            plugins[family] = registered
            builtins[family] = builtin_names
            combined[family] = sorted(set(registered) | set(builtin_names))
        payload["service_providers"] = combined
        payload["service_provider_builtins"] = builtins
        payload["service_provider_plugins"] = plugins

    def tools() -> None:
        from tools.registry import discover_builtin_tools, registry

        payload["imported_tool_modules"] = _sorted_strings(discover_builtin_tools())
        payload["tools"] = _sorted_strings(registry.get_all_tool_names())
        payload["tool_to_toolset"] = {
            str(key): str(value)
            for key, value in sorted(registry.get_tool_to_toolset_map().items())
        }

        from toolsets import get_all_toolsets

        toolsets = get_all_toolsets()
        direct: dict[str, list[str]] = {}
        includes: dict[str, list[str]] = {}
        for name, config in sorted(toolsets.items()):
            if not isinstance(config, Mapping):
                continue
            direct[str(name)] = _sorted_strings(config.get("tools", []))
            includes[str(name)] = _sorted_strings(config.get("includes", []))
        payload["toolsets"] = direct
        payload["toolset_includes"] = includes

    for section, callback in (
        ("platforms", platforms),
        ("provider_profiles", providers),
        ("auth_providers", auth_providers),
        ("canonical_providers", canonical_providers),
        ("model_catalog", model_catalog),
        ("transports", transports),
        ("service_providers", service_providers),
        ("tools", tools),
    ):
        _capture(payload, section, callback)

    payload["probe_errors"] = sorted(set(payload["probe_errors"]))
    return payload


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    print(json.dumps(collect_snapshot(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
