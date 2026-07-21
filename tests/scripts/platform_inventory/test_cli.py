import json
from pathlib import Path

from scripts.platform_inventory.cli import main


def test_cli_writes_source_state_json(monkeypatch, tmp_path: Path) -> None:
    from scripts.platform_inventory.models import SourceState

    monkeypatch.setattr(
        "scripts.platform_inventory.cli.read_source_state",
        lambda root: SourceState(
            root.resolve(), "test", "a" * 40, False, {"origin": "example"}
        ),
    )
    output = tmp_path / "generated"

    assert main(["--root", str(tmp_path), "--output", str(output), "source-state"]) == 0
    payload = json.loads((output / "source-state.json").read_text(encoding="utf-8"))
    assert payload["head_sha"] == "a" * 40
    assert payload["branch"] == "test"


def test_generate_writes_reports_and_returns_zero(monkeypatch, tmp_path: Path) -> None:
    from scripts.platform_inventory.models import (
        DependencyMap,
        FrontendMap,
        PythonGraph,
        RegistrySnapshot,
        SourceState,
    )

    monkeypatch.setattr(
        "scripts.platform_inventory.cli.read_source_state",
        lambda root: SourceState(root.resolve(), "test", "b" * 40, False, {}),
    )
    monkeypatch.setattr(
        "scripts.platform_inventory.cli.discover_plugins", lambda *args: []
    )
    monkeypatch.setattr(
        "scripts.platform_inventory.cli.scan_python_graph",
        lambda *args: PythonGraph((), (), (), ()),
    )
    monkeypatch.setattr(
        "scripts.platform_inventory.cli.probe_runtime",
        lambda *args: RegistrySnapshot(
            (), (), (), (), {}, (), (), (), (), {}, {}, (), {}, (), ()
        ),
    )
    monkeypatch.setattr(
        "scripts.platform_inventory.cli.scan_frontend",
        lambda *args: FrontendMap((), (), (), (), ()),
    )
    monkeypatch.setattr(
        "scripts.platform_inventory.cli.scan_dependencies",
        lambda *args: DependencyMap((), {}, {}, {}),
    )
    output = tmp_path / "generated"

    assert main(["--root", str(tmp_path), "--output", str(output), "generate"]) == 0
    assert (output / "inventory.json").exists()
    assert (output / "phase-0-review.md").exists()


def test_generate_writes_reports_and_returns_two_on_probe_errors(
    monkeypatch, tmp_path: Path
) -> None:
    from scripts.platform_inventory.models import (
        DependencyMap,
        FrontendMap,
        InventoryReport,
        PythonGraph,
        RegistrySnapshot,
        SourceState,
    )

    report = InventoryReport(
        schema_version=1,
        source=SourceState(tmp_path, "test", "c" * 40, False, {}),
        plugins=(),
        python_graph=PythonGraph((), (), (), ()),
        registries=RegistrySnapshot(
            (),
            (),
            (),
            (),
            {},
            (),
            (),
            (),
            (),
            {},
            {},
            (),
            {},
            (),
            ("providers:ImportError:broken",),
        ),
        frontend=FrontendMap((), (), (), (), ()),
        dependencies=DependencyMap((), {}, {}, {}),
    )
    monkeypatch.setattr(
        "scripts.platform_inventory.cli.build_inventory", lambda root: report
    )
    output = tmp_path / "generated"

    assert main(["--root", str(tmp_path), "--output", str(output), "generate"]) == 2
    assert "providers:ImportError:broken" in (
        output / "phase-0-review.md"
    ).read_text(encoding="utf-8")
