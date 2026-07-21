from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.platform_inventory.cli import build_inventory
from scripts.platform_inventory.reports import blocking_findings, write_reports


REQUIRED_REPOSITORY_PATHS = (
    Path("gateway"),
    Path("providers"),
    Path("hermes_cli"),
    Path("agent"),
    Path("plugins"),
    Path("pyproject.toml"),
)


def _is_full_hermes_checkout(root: Path) -> bool:
    return all((root / path).exists() for path in REQUIRED_REPOSITORY_PATHS)


def _hashes(paths: tuple[Path, ...]) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


@pytest.mark.skipif(
    not _is_full_hermes_checkout(Path.cwd()),
    reason="requires the complete Hermes repository checkout",
)
def test_full_repository_inventory_is_complete_and_deterministic(tmp_path: Path) -> None:
    root = Path.cwd()
    report = build_inventory(root)

    assert report.source.dirty is False
    assert report.plugins, "expected plugin manifests"
    assert report.registries.platforms, "expected messaging platforms"
    assert report.registries.canonical_providers, "expected AI providers"
    assert report.registries.tools, "expected registered tools"
    assert report.frontend.routes, "expected browser routes"
    assert blocking_findings(report) == ()

    first_paths = write_reports(report, tmp_path / "first")
    second_paths = write_reports(report, tmp_path / "second")

    assert len(first_paths) == 9
    assert _hashes(first_paths) == _hashes(second_paths)

    print(
        "phase0_inventory_summary",
        {
            "plugins": len(report.plugins),
            "platforms": len(report.registries.platforms),
            "canonical_providers": len(report.registries.canonical_providers),
            "service_provider_families": {
                key: len(value)
                for key, value in report.registries.service_providers.items()
            },
            "tools": len(report.registries.tools),
            "toolsets": len(report.registries.toolsets),
            "frontend_routes": len(report.frontend.routes),
            "python_files": len(report.python_graph.files),
        },
    )
