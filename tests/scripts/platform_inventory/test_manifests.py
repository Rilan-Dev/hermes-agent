from pathlib import Path

import pytest

from scripts.platform_inventory.manifests import discover_plugins
from scripts.platform_inventory.models import InventoryError


FIXTURE = Path("tests/fixtures/platform_inventory/plugins")


def test_discover_plugins_finds_recursive_manifest_children() -> None:
    records = discover_plugins(FIXTURE, [Path(".")])

    assert [(r.kind, r.plugin_key) for r in records] == [
        ("backend", "image_gen/openai"),
        ("backend", "tts/openai"),
        ("model-provider", "model-providers/example"),
        ("platform", "platforms/telegram"),
        ("standalone", "cron_providers/chronos"),
    ]
    telegram = next(r for r in records if r.plugin_key == "platforms/telegram")
    assert telegram.plugin_id == "telegram"
    assert telegram.category == "platforms"
    assert telegram.manifest_name == "telegram-platform"
    assert telegram.label == "Telegram"
    assert telegram.required_env == ("TELEGRAM_BOT_TOKEN",)
    assert telegram.optional_env == ("TELEGRAM_ALLOWED_USERS",)
    assert "platforms/telegram/plugin.yaml" in telegram.files
    assert "platforms/telegram/__init__.py" in telegram.files


def test_duplicate_leaf_names_keep_distinct_plugin_keys() -> None:
    records = discover_plugins(FIXTURE, [Path(".")])
    openai = [r for r in records if r.plugin_id == "openai"]

    assert [r.plugin_key for r in openai] == ["image_gen/openai", "tts/openai"]
    image = next(r for r in openai if r.plugin_key == "image_gen/openai")
    assert image.provides_tools == ("image_generate",)
    assert image.provides_hooks == ("pre_tool_call",)


def test_discover_plugins_defaults_omitted_kind_to_standalone() -> None:
    records = discover_plugins(FIXTURE, [Path(".")])
    chronos = next(
        record for record in records if record.plugin_key == "cron_providers/chronos"
    )

    assert chronos.kind == "standalone"


def test_discover_plugins_rejects_explicit_blank_kind(tmp_path: Path) -> None:
    plugin = tmp_path / "platforms" / "broken"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text("name: broken\nkind: ''\n", encoding="utf-8")

    with pytest.raises(InventoryError, match="blank kind"):
        discover_plugins(tmp_path, [Path("platforms")])
