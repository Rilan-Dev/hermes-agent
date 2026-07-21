from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _probe_environment(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "HERMES_HOME": str(tmp_path / "home"),
            "HERMES_ENABLE_PROJECT_PLUGINS": "0",
            "HERMES_SAFE_MODE": "0",
            "HERMES_PLUGINS_DEBUG": "0",
            "PYTHONHASHSEED": "0",
        }
    )
    return env


def test_registry_probe_is_deterministic_and_isolated(tmp_path: Path) -> None:
    command = [sys.executable, "-m", "scripts.extraction.registry_probe"]
    env = _probe_environment(tmp_path)

    first = subprocess.run(
        command, check=True, env=env, text=True, capture_output=True
    )
    second = subprocess.run(
        command, check=True, env=env, text=True, capture_output=True
    )

    assert first.stdout == second.stdout
    data = json.loads(first.stdout)
    assert data["provider_catalog_slugs"] == data["canonical_providers"]
    assert "openai-api" in data["canonical_providers"]
    assert "openai-codex" in data["canonical_providers"]
    assert "openai" not in data["canonical_providers"]
    assert set(data["platform_registry"]) == (
        set(data["platform_concrete"]) | set(data["platform_deferred"])
    )
    assert data["network_access_blocked"] is True


def test_registry_probe_contains_only_serializable_metadata(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "scripts.extraction.registry_probe"],
        check=True,
        env=_probe_environment(tmp_path),
        text=True,
        capture_output=True,
    )
    data = json.loads(result.stdout)

    assert all(isinstance(row["key"], str) for row in data["plugins"])
    assert all(
        isinstance(row["api_key_env_vars"], list)
        for row in data["provider_catalog"]
    )
    assert all(
        set(row) == {
            "name",
            "label",
            "source",
            "plugin_name",
            "required_env",
            "max_message_length",
            "pii_safe",
            "cron_deliver_env_var",
            "has_standalone_sender",
        }
        for row in data["platform_concrete_metadata"]
    )
