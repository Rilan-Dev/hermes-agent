from pathlib import Path

import pytest

from scripts.platform_inventory.manifests import discover_plugins
from scripts.platform_inventory.models import InventoryError


FIXTURE = Path("tests/fixtures/platform_inventory/plugins")


def test_discover_plugins_finds_all_manifest_children() -> None:
    records = discover_plugins(
        FIXTURE,
        [Path("platforms"), Path("model-providers")],
    )

    assert [(r.kind, r.plugin_id) for r in records] == [
        ("model-provider", "example"),
        ("platform", "telegram"),
    ]
    telegram = next(r for r in records if r.plugin_id == "telegram")
    assert telegram.manifest_name == "telegram-platform"
    assert telegram.label == "Telegram"
    assert telegram.required_env == ("TELEGRAM_BOT_TOKEN",)
    assert telegram.optional_env == ("TELEGRAM_ALLOWED_USERS",)
    assert "platforms/telegram/plugin.yaml" in telegram.files
    assert "platforms/telegram/__init__.py" in telegram.files


def test_discover_plugins_rejects_missing_kind(tmp_path: Path) -> None:
    plugin = tmp_path / "platforms" / "broken"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text("name: broken\n", encoding="utf-8")

    with pytest.raises(InventoryError, match="missing kind"):
        discover_plugins(tmp_path, [Path("platforms")])
