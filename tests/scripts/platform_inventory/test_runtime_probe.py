import json
import os
from pathlib import Path

import pytest

from scripts.platform_inventory.models import InventoryError
from scripts.platform_inventory.runtime_probe import parse_probe_output, probe_runtime


def _payload() -> dict:
    return {
        "platforms": ["telegram"],
        "platform_concrete": [],
        "platform_deferred": ["telegram"],
        "provider_profiles": ["openai-api"],
        "provider_aliases": {"openai": "openai-api"},
        "auth_providers": ["openai-api", "openai-codex"],
        "canonical_providers": ["openai-api"],
        "model_catalog_providers": ["openai", "openai-api"],
        "transports": ["chat_completions", "codex"],
        "toolsets": {"web": ["web_extract", "web_search"]},
        "toolset_includes": {"web": []},
        "tools": ["web_extract", "web_search"],
        "tool_to_toolset": {"web_extract": "web", "web_search": "web"},
        "imported_tool_modules": ["tools.web_tools"],
        "probe_errors": [],
    }


def test_parse_probe_output_keeps_identifier_sets_separate() -> None:
    snapshot = parse_probe_output(json.dumps(_payload()))

    assert snapshot.auth_providers == ("openai-api", "openai-codex")
    assert snapshot.model_catalog_providers == ("openai", "openai-api")
    assert snapshot.provider_aliases == {"openai": "openai-api"}
    assert snapshot.platform_deferred == ("telegram",)
    assert snapshot.tool_to_toolset["web_search"] == "web"


def test_parse_probe_output_sorts_and_deduplicates() -> None:
    payload = _payload()
    payload["platforms"] = ["telegram", "discord", "telegram"]
    payload["tools"] = ["web_search", "web_extract", "web_search"]

    snapshot = parse_probe_output(json.dumps(payload))

    assert snapshot.platforms == ("discord", "telegram")
    assert snapshot.tools == ("web_extract", "web_search")


def test_parse_probe_output_rejects_invalid_json() -> None:
    with pytest.raises(InventoryError, match="invalid runtime probe JSON"):
        parse_probe_output("not-json")


def test_parse_probe_output_rejects_wrong_shapes() -> None:
    payload = _payload()
    payload["provider_aliases"] = []

    with pytest.raises(InventoryError, match="provider_aliases must be an object"):
        parse_probe_output(json.dumps(payload))


def test_probe_runtime_uses_isolated_home(monkeypatch, tmp_path: Path) -> None:
    observed: dict[str, str] = {}

    class Result:
        returncode = 0
        stdout = json.dumps(_payload())
        stderr = ""

    def fake_run(command, **kwargs):
        observed.update(kwargs["env"])
        assert command[-1] == "scripts.platform_inventory.probe_entrypoint"
        return Result()

    monkeypatch.setattr(
        "scripts.platform_inventory.runtime_probe.subprocess.run", fake_run
    )

    probe_runtime(tmp_path)

    assert observed["HERMES_HOME"]
    assert observed["HERMES_PROFILE"] == "inventory"
    assert observed["HERMES_INVENTORY_MODE"] == "1"
    assert observed["HERMES_ENABLE_PROJECT_PLUGINS"] == "0"
    assert observed["PYTHONPATH"].split(os.pathsep)[0] == str(tmp_path.resolve())


def test_probe_runtime_wraps_nonzero_exit(monkeypatch, tmp_path: Path) -> None:
    class Result:
        returncode = 3
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(
        "scripts.platform_inventory.runtime_probe.subprocess.run",
        lambda *args, **kwargs: Result(),
    )

    with pytest.raises(InventoryError, match="runtime probe failed: boom"):
        probe_runtime(tmp_path)
