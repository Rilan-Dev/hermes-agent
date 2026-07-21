from pathlib import Path

import pytest

from scripts.extraction.plugin_inventory import (
    PluginInventoryError,
    inventory_plugins,
)


def test_plugin_inventory_never_imports_plugin_module(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins/platforms/example"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text(
        "name: example\nkind: platform\nversion: 1.0.0\n",
        encoding="utf-8",
    )
    (plugin / "__init__.py").write_text(
        "raise RuntimeError('must not import')\n", encoding="utf-8"
    )

    records = inventory_plugins(tmp_path, ("plugins/platforms",))

    assert records[0].name == "example"
    assert records[0].key == "example"
    assert records[0].kind == "platform"
    assert records[0].module_path == "plugins/platforms/example/__init__.py"


def test_plugin_inventory_is_sorted_by_kind_key_and_name(tmp_path: Path) -> None:
    for key, kind in (("zeta", "platform"), ("alpha", "model-provider")):
        plugin = tmp_path / f"plugins/catalog/{key}"
        plugin.mkdir(parents=True)
        (plugin / "plugin.yaml").write_text(
            f"name: {key}\nkind: {kind}\n", encoding="utf-8"
        )
        (plugin / "__init__.py").write_text("", encoding="utf-8")

    records = inventory_plugins(tmp_path, ("plugins/catalog",))

    assert [(item.kind, item.key, item.name) for item in records] == [
        ("model-provider", "alpha", "alpha"),
        ("platform", "zeta", "zeta"),
    ]


def test_plugin_inventory_rejects_missing_name(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins/platforms/broken"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text(
        "kind: platform\n", encoding="utf-8"
    )

    with pytest.raises(PluginInventoryError, match="name"):
        inventory_plugins(tmp_path, ("plugins/platforms",))
