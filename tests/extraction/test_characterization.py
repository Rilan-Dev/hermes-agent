from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml

_INVENTORY_PATH = Path("docs/extraction/generated/phase-1-inventory.yaml")
_REGISTRY_PATH = Path("tests/extraction/snapshots/registry-snapshot.json")


@lru_cache(maxsize=1)
def inventory() -> dict[str, object]:
    data = yaml.safe_load(_INVENTORY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


@lru_cache(maxsize=1)
def registry() -> dict[str, object]:
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_platform_manifests_match_discovered_platform_plugins() -> None:
    manifest_names = {
        item["name"] for item in inventory()["plugins"]["platforms"]
    }
    registry_keys = {
        item["key"]
        for item in registry()["plugins"]
        if item["kind"] == "platform"
    }
    assert manifest_names == registry_keys


def test_model_provider_manifests_register_provider_profiles() -> None:
    manifest_keys = {
        item["key"]
        for item in inventory()["plugins"]["model_providers"]
    }
    profile_names = set(registry()["provider_profile_names"])

    assert manifest_keys <= profile_names
    assert profile_names - manifest_keys == {
        "kimi-coding-cn",
        "minimax-cn",
        "minimax-oauth",
        "opencode-go",
    }


def test_provider_catalog_preserves_canonical_order() -> None:
    data = registry()
    assert data["provider_catalog_slugs"] == data["canonical_providers"]
    assert "openai-api" in data["canonical_providers"]
    assert "openai-codex" in data["canonical_providers"]
    assert "openai" not in data["canonical_providers"]


def test_required_onboarding_surfaces_are_scoped() -> None:
    sources = {item["source"] for item in inventory()["files"]}
    assert {
        "agent/onboarding.py",
        "hermes_cli/setup.py",
        "hermes_cli/model_setup_flows.py",
        "hermes_cli/gateway.py",
        "apps/desktop/src/components/onboarding/index.tsx",
        "apps/desktop/src/store/onboarding.ts",
        "web/src/components/OAuthProvidersCard.tsx",
        "web/src/lib/api.ts",
    } <= sources


def test_no_unresolved_internal_imports() -> None:
    assert inventory()["unresolved_imports"] == []


def test_generated_reports_match_the_implementation_head() -> None:
    data = inventory()
    assert data["schema_version"] == 1
    assert data["source_sha"] == "d7b36070ef807841699ad32c5b6af547fee3ff64"
    assert isinstance(data["inventory_head"], str)
    assert len(data["inventory_head"]) == 40
