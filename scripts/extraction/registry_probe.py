from __future__ import annotations

import json
import socket
from typing import Any, NoReturn


def _network_disabled(*_args: object, **_kwargs: object) -> NoReturn:
    raise OSError("network access is disabled during extraction registry probing")


def _block_network_access() -> None:
    socket.create_connection = _network_disabled  # type: ignore[assignment]
    socket.getaddrinfo = _network_disabled  # type: ignore[assignment]
    socket.socket.connect = _network_disabled  # type: ignore[assignment]
    socket.socket.connect_ex = _network_disabled  # type: ignore[assignment]


def _string_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    try:
        return [str(item) for item in value]  # type: ignore[union-attr]
    except TypeError:
        return [str(value)]


def _platform_metadata(entry: object) -> dict[str, object]:
    return {
        "name": str(getattr(entry, "name", "")),
        "label": str(getattr(entry, "label", "")),
        "source": str(getattr(entry, "source", "")),
        "plugin_name": str(getattr(entry, "plugin_name", "")),
        "required_env": _string_list(getattr(entry, "required_env", ())),
        "max_message_length": int(getattr(entry, "max_message_length", 0) or 0),
        "pii_safe": bool(getattr(entry, "pii_safe", False)),
        "cron_deliver_env_var": str(
            getattr(entry, "cron_deliver_env_var", "") or ""
        ),
        "has_standalone_sender": callable(
            getattr(entry, "standalone_sender_fn", None)
        ),
    }


def _profile_metadata(profile: object) -> dict[str, object]:
    return {
        "name": str(getattr(profile, "name", "")),
        "aliases": _string_list(getattr(profile, "aliases", ())),
        "auth_type": str(getattr(profile, "auth_type", "") or ""),
        "env_vars": _string_list(getattr(profile, "env_vars", ())),
        "api_mode": str(getattr(profile, "api_mode", "") or ""),
        "base_url": str(getattr(profile, "base_url", "") or ""),
        "supports_health_check": bool(
            getattr(profile, "supports_health_check", True)
        ),
        "supports_vision": bool(getattr(profile, "supports_vision", False)),
    }


def _auth_metadata(provider_id: str, config: object) -> dict[str, object]:
    return {
        "id": provider_id,
        "name": str(getattr(config, "name", "")),
        "auth_type": str(getattr(config, "auth_type", "") or ""),
        "api_key_env_vars": _string_list(
            getattr(config, "api_key_env_vars", ())
        ),
        "base_url_env_var": str(
            getattr(config, "base_url_env_var", "") or ""
        ),
        "inference_base_url": str(
            getattr(config, "inference_base_url", "") or ""
        ),
    }


def _catalog_metadata(descriptor: object) -> dict[str, object]:
    return {
        "slug": str(getattr(descriptor, "slug", "")),
        "label": str(getattr(descriptor, "label", "")),
        "description": str(getattr(descriptor, "description", "")),
        "auth_type": str(getattr(descriptor, "auth_type", "") or ""),
        "tab": str(getattr(descriptor, "tab", "")),
        "api_key_env_vars": _string_list(
            getattr(descriptor, "api_key_env_vars", ())
        ),
        "base_url_env_var": str(
            getattr(descriptor, "base_url_env_var", "") or ""
        ),
        "signup_url": str(getattr(descriptor, "signup_url", "") or ""),
        "order": int(getattr(descriptor, "order", 0)),
    }


def build_registry_snapshot() -> dict[str, Any]:
    _block_network_access()

    from gateway.platform_registry import platform_registry
    from hermes_cli.auth import PROVIDER_REGISTRY
    from hermes_cli.models import CANONICAL_PROVIDERS
    from hermes_cli.plugins import discover_plugins, get_plugin_manager
    from hermes_cli.provider_catalog import provider_catalog
    from providers import list_providers

    discover_plugins(force=True)
    plugins = sorted(
        get_plugin_manager().list_plugins(),
        key=lambda row: (str(row.get("kind", "")), str(row.get("key", ""))),
    )
    profiles = sorted(list_providers(), key=lambda profile: profile.name)
    catalog = provider_catalog()

    concrete_by_name = dict(platform_registry._entries)
    deferred_names = sorted(platform_registry._deferred)
    concrete_names = sorted(concrete_by_name)
    platform_names = sorted(set(concrete_names) | set(deferred_names))

    auth_provider_ids = sorted(PROVIDER_REGISTRY)
    canonical_provider_slugs = [entry.slug for entry in CANONICAL_PROVIDERS]

    return {
        "schema_version": 1,
        "network_access_blocked": True,
        "plugins": plugins,
        "platform_registry": platform_names,
        "platform_concrete": concrete_names,
        "platform_deferred": deferred_names,
        "platform_concrete_metadata": [
            _platform_metadata(concrete_by_name[name]) for name in concrete_names
        ],
        "provider_profiles": [_profile_metadata(profile) for profile in profiles],
        "provider_profile_names": [profile.name for profile in profiles],
        "canonical_providers": canonical_provider_slugs,
        "auth_providers": auth_provider_ids,
        "auth_provider_metadata": [
            _auth_metadata(provider_id, PROVIDER_REGISTRY[provider_id])
            for provider_id in auth_provider_ids
        ],
        "provider_catalog": [_catalog_metadata(item) for item in catalog],
        "provider_catalog_slugs": [item.slug for item in catalog],
    }


def main() -> None:
    print(
        json.dumps(
            build_registry_snapshot(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
