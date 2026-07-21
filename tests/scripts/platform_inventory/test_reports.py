import json
from dataclasses import replace
from pathlib import Path

import yaml

from scripts.platform_inventory.models import (
    DependencyMap,
    FrontendMap,
    InventoryReport,
    PythonGraph,
    RegistrySnapshot,
    SourceState,
)
from scripts.platform_inventory.reports import blocking_findings, write_reports


def _report(tmp_path: Path, *, dirty: bool = False, errors: tuple[str, ...] = ()) -> InventoryReport:
    return InventoryReport(
        schema_version=1,
        source=SourceState(tmp_path, "main", "a" * 40, dirty, {}),
        plugins=(),
        python_graph=PythonGraph((), (), (), ()),
        registries=RegistrySnapshot(
            platforms=(),
            platform_concrete=(),
            platform_deferred=(),
            provider_profiles=(),
            provider_aliases={},
            auth_providers=(),
            canonical_providers=(),
            model_catalog_providers=(),
            transports=(),
            toolsets={},
            toolset_includes={},
            tools=(),
            tool_to_toolset={},
            imported_tool_modules=(),
            probe_errors=errors,
        ),
        frontend=FrontendMap((), (), (), (), ()),
        dependencies=DependencyMap((), {}, {}, {}),
    )


def test_write_reports_is_deterministic_and_creates_review_files(tmp_path: Path) -> None:
    report = _report(tmp_path)

    paths = write_reports(report, tmp_path / "out")
    first = {path.name: path.read_bytes() for path in paths}
    paths = write_reports(report, tmp_path / "out")
    second = {path.name: path.read_bytes() for path in paths}

    assert first == second
    assert set(first) == {
        "source-state.json",
        "inventory.json",
        "extraction-manifest.yaml",
        "channel-capabilities.md",
        "provider-capabilities.md",
        "tool-capabilities.md",
        "frontend-api-map.md",
        "dependency-test-map.md",
        "phase-0-review.md",
    }
    payload = json.loads((tmp_path / "out" / "inventory.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["source"]["head_sha"] == "a" * 40
    assert payload["source"]["root"] == "."
    manifest = yaml.safe_load(
        (tmp_path / "out" / "extraction-manifest.yaml").read_text(encoding="utf-8")
    )
    assert manifest["version"] == 1
    assert manifest["source"]["sha"] == "a" * 40


def test_blocking_findings_include_dirty_probe_and_import_errors(tmp_path: Path) -> None:
    report = _report(tmp_path, dirty=True, errors=("tools:ImportError:missing",))
    report = replace(
        report, python_graph=PythonGraph((), (), (), ("gateway/run.py:missing",))
    )

    assert blocking_findings(report) == (
        "source worktree is dirty",
        "runtime probe error: tools:ImportError:missing",
        "unresolved local import: gateway/run.py:missing",
    )
