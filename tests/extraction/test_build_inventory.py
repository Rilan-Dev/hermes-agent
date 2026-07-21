from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.extraction.build_inventory import (
    SourceGuardError,
    build_inventory,
    verify_source_guard,
)
from scripts.extraction.render_report import (
    render_inventory_markdown,
    render_test_matrix,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def _fixture_repository(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    plugin = repo / "plugins/platforms/chat"
    plugin.mkdir(parents=True)
    (repo / "gateway").mkdir()
    (repo / "gateway/__init__.py").write_text("", encoding="utf-8")
    (repo / "gateway/session.py").write_text(
        "from gateway import delivery\nimport json\n", encoding="utf-8"
    )
    (repo / "gateway/delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    (plugin / "__init__.py").write_text("", encoding="utf-8")
    (plugin / "plugin.yaml").write_text(
        "name: chat\nkind: platform\nversion: 1.0.0\n",
        encoding="utf-8",
    )

    _git(repo, "init")
    _git(repo, "config", "user.email", "inventory@example.invalid")
    _git(repo, "config", "user.name", "Inventory Tests")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fixture")
    source_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        f"""version: 1
source_repository: Rilan-Dev/hermes-agent
source_sha: {source_sha}
dynamic_roots:
  - path: plugins/platforms
    classification: core
    destination: vendor/plugins/platforms
    reason: platform plugins
explicit_files:
  - path: gateway/session.py
    classification: core
    destination: vendor/gateway/session.py
    reason: canonical sessions
  - path: gateway/delivery.py
    classification: host_port
    destination: compatibility/gateway/delivery.py
    reason: host delivery
 test_rules: []
internal_module_roots:
  - gateway
""".replace("\n test_rules:", "\ntest_rules:"),
        encoding="utf-8",
    )

    snapshot_path = repo / "registry.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "platform_registry": ["chat"],
                "platform_concrete": [],
                "platform_deferred": ["chat"],
                "provider_profiles": [],
                "canonical_providers": ["openai-api", "openai-codex"],
                "auth_providers": ["openai-api", "openai-codex"],
                "provider_catalog": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return repo, manifest_path, snapshot_path


def test_build_inventory_is_deterministic(tmp_path: Path) -> None:
    repo, manifest_path, snapshot_path = _fixture_repository(tmp_path)

    first = build_inventory(repo, manifest_path, snapshot_path)
    second = build_inventory(repo, manifest_path, snapshot_path)

    assert first == second
    assert first["files"]
    assert first["plugins"]["platforms"][0]["key"] == "chat"
    assert first["registries"]["canonical_providers"] == [
        "openai-api",
        "openai-codex",
    ]
    assert first["out_of_scope_imports"] == []
    assert first["unresolved_imports"] == []
    yaml.safe_dump(first, sort_keys=False, allow_unicode=True)


def test_source_guard_rejects_scoped_drift(tmp_path: Path) -> None:
    repo, manifest_path, _snapshot_path = _fixture_repository(tmp_path)
    (repo / "gateway/session.py").write_text("VALUE = 2\n", encoding="utf-8")

    with pytest.raises(SourceGuardError, match="scoped production source differs"):
        verify_source_guard(repo, manifest_path)


def test_markdown_renderers_are_stable(tmp_path: Path) -> None:
    repo, manifest_path, snapshot_path = _fixture_repository(tmp_path)
    data = build_inventory(repo, manifest_path, snapshot_path)

    inventory_markdown = render_inventory_markdown(data)
    matrix_markdown = render_test_matrix(data["test_rules"])

    assert inventory_markdown.startswith("# Phase 1 Extraction Inventory\n")
    assert "## Classification Counts" in inventory_markdown
    assert "## Out-of-Scope Internal Dependencies" in inventory_markdown
    assert matrix_markdown.startswith("# Phase 1 Test Matrix\n")
